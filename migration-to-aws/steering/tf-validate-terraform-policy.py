#!/usr/bin/env python3
"""Static policy checks on generated Terraform (no provider init required).

Read-only VERDICT PRODUCER. This script never edits .tf files and never touches
run state (.phase-status.json). It parses HCL, evaluates policy, and emits a
structured verdict (stdout summary + optional --json report). Remediation and any
phase/state decisions belong to the CALLER (see tf-best-practices tf-best-practices.md).

Enforces (each rule is fail-open on ambiguity — fires only on unambiguous,
in-block literal evidence, so a valid stack is never falsely blocked):
  - Internet-facing ALB TLS posture:
      * HTTPS listener on port 443 with certificate_arn and a forward action
      * HTTP listener on port 80 must redirect to HTTPS (never forward to targets)
  - rds_not_public: aws_db_instance / aws_rds_cluster must not set
    publicly_accessible = true (fail-open when variable-driven or absent).
  - db_sg_no_public_ingress: an inline aws_security_group ingress covering a
    database port (5432 / 3306) must not allow 0.0.0.0/0 (fail-open on
    separate aws_security_group_rule / aws_vpc_security_group_ingress_rule
    resources, which this static reader cannot correlate).
  - sg_no_public_admin_ingress: an inline ingress must not open a well-known
    admin/datastore port (SSH, RDP, Redis, Memcached, Mongo, Elasticsearch,
    Kibana) to 0.0.0.0/0. Scoped to a fixed never-public port list — web ports
    and app/game ports are not flagged. Same inline-only fail-open scope.
  - no_wildcard_iam: a literal IAM policy document with Effect "Allow" must not
    use Action "*" or Resource "*" (fail-open on aws_iam_policy_document data
    sources, whose statements are not visible as literal JSON here).
  - rds_encryption_at_rest: aws_db_instance / aws_rds_cluster must set
    storage_encrypted = true (RDS defaults to UNENCRYPTED). Fail-open when
    variable-driven. S3 is intentionally NOT checked: buckets have default
    SSE-S3 since Jan 2023, so a missing SSE block is not an unencrypted bucket.
  - elasticache_encryption_at_rest: aws_elasticache_replication_group must set
    at_rest_encryption_enabled = true. Fail-open when variable-driven.

Usage:
  python3 tf-validate-terraform-policy.py /path/to/terraform [--json report.json]

Exit 0 on POLICY_OK, 1 on POLICY_FAIL, 2 on usage/IO error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

RESOURCE_OPEN = re.compile(
    r'resource\s+"(?P<type>[a-zA-Z0-9_]+)"\s+"(?P<name>[^"]+)"\s*\{',
    re.MULTILINE,
)


@dataclass(frozen=True)
class Violation:
    check: str          # "policy"
    rule: str           # "alb_https_listener" | "alb_http_redirect" | "no_tf_files"
                        # | "rds_not_public" | "db_sg_no_public_ingress"
                        # | "no_wildcard_iam" | "rds_encryption_at_rest"
    file: str
    line: int           # 1-based; 0 if unknown
    severity: str       # "error" | "warning"
    summary: str
    fix_hint: str


@dataclass(frozen=True)
class ListenerSpec:
    file: str
    name: str
    line: int
    port: int | None
    protocol: str | None
    action_type: str | None
    has_certificate_arn: bool


def _read_tf_files(terraform_dir: Path) -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    for path in sorted(terraform_dir.rglob("*.tf")):
        files.append((str(path.relative_to(terraform_dir)), path.read_text(encoding="utf-8")))
    return files


def _extract_braced_block(content: str, open_brace: int) -> tuple[str, int]:
    """Return (block_text_including_braces, index_after_close). Brace-depth aware."""
    depth = 0
    for idx in range(open_brace, len(content)):
        char = content[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[open_brace : idx + 1], idx + 1
    return content[open_brace:], len(content)


def _extract_blocks(content: str, resource_type: str) -> list[tuple[str, str, int]]:
    """Return (name, body, 1-based line) for each resource of resource_type."""
    blocks: list[tuple[str, str, int]] = []
    for match in RESOURCE_OPEN.finditer(content):
        if match.group("type") != resource_type:
            continue
        name = match.group("name")
        brace_start = match.end() - 1
        body, _ = _extract_braced_block(content, brace_start)
        line = content.count("\n", 0, match.start()) + 1
        blocks.append((name, body, line))
    return blocks


def _attr_string(block: str, attr: str) -> str | None:
    match = re.search(rf'^\s*{re.escape(attr)}\s*=\s*"([^"]*)"', block, re.MULTILINE)
    if match:
        return match.group(1)
    bool_match = re.search(
        rf"^\s*{re.escape(attr)}\s*=\s*(true|false)\b",
        block,
        re.MULTILINE | re.IGNORECASE,
    )
    return bool_match.group(1).lower() if bool_match else None


def _attr_int(block: str, attr: str) -> int | None:
    match = re.search(rf"^\s*{re.escape(attr)}\s*=\s*(\d+)", block, re.MULTILINE)
    return int(match.group(1)) if match else None


def _default_action_type(block: str) -> str | None:
    """Extract default_action { ... type = "X" ... } via BRACE-DEPTH matching.

    NOTE: the naive r'default_action\\s*\\{[^}]*?type' approach breaks when the
    default_action contains a nested block (redirect {} / forward {}) placed
    BEFORE the type attribute — it stops at the first '}'. We isolate the full
    default_action body by brace matching, then read `type` from it.
    """
    m = re.search(r"default_action\s*\{", block)
    if not m:
        return None
    body, _ = _extract_braced_block(block, m.end() - 1)
    tmatch = re.search(r'^\s*type\s*=\s*"([^"]+)"', body, re.MULTILINE)
    return tmatch.group(1) if tmatch else None


def _has_internet_facing_alb(tf_files: list[tuple[str, str]]) -> bool:
    """True if any aws_lb is an internet-facing APPLICATION load balancer.

    The HTTPS-listener posture applies only to Application Load Balancers (L7).
    Network (L4 TCP/UDP) and Gateway (L3) load balancers legitimately have no
    HTTPS:443 listener, so an internet-facing NLB/GWLB must NOT be flagged.

    - load_balancer_type == "network" | "gateway" (literal) => skip (not an ALB).
    - load_balancer_type absent (Terraform default is "application"),
      "application", or variable-driven => treat as an ALB (fail-safe).
    - internal absent, "false", or variable-driven => internet-facing (fail-safe:
      demand HTTPS unless explicitly internal=true).
    """
    for _, content in tf_files:
        for _, body, _line in _extract_blocks(content, "aws_lb"):
            lb_type = _attr_string(body, "load_balancer_type")
            if lb_type in ("network", "gateway"):
                continue  # L4/L3 balancer — HTTPS-listener rule does not apply
            internal = _attr_string(body, "internal")
            if internal is None or internal == "false":
                return True
    return False


def _parse_listeners(tf_files: list[tuple[str, str]]) -> list[ListenerSpec]:
    listeners: list[ListenerSpec] = []
    for rel_path, content in tf_files:
        for name, body, line in _extract_blocks(content, "aws_lb_listener"):
            listeners.append(
                ListenerSpec(
                    file=rel_path,
                    name=name,
                    line=line,
                    port=_attr_int(body, "port"),
                    protocol=_attr_string(body, "protocol"),
                    action_type=_default_action_type(body),
                    has_certificate_arn="certificate_arn" in body,
                )
            )
    return listeners


def check_alb_https_policy(terraform_dir: Path) -> list[Violation]:
    tf_files = _read_tf_files(terraform_dir)
    if not tf_files:
        return [
            Violation(
                check="policy",
                rule="no_tf_files",
                file=".",
                line=0,
                severity="error",
                summary="No .tf files found in terraform directory",
                fix_hint="Ensure the generate step wrote terraform/ before validation",
            )
        ]

    if not _has_internet_facing_alb(tf_files):
        return []

    listeners = _parse_listeners(tf_files)
    violations: list[Violation] = []

    https_ok = [
        l
        for l in listeners
        if l.port == 443
        and (l.protocol or "").upper() == "HTTPS"
        and l.has_certificate_arn
        and l.action_type == "forward"
    ]

    if not https_ok:
        # Point at an aws_lb file when we can, else the first tf file.
        lb_file = next(
            (rel for rel, c in tf_files if _extract_blocks(c, "aws_lb")),
            tf_files[0][0],
        )
        violations.append(
            Violation(
                check="policy",
                rule="alb_https_listener",
                file=lb_file,
                line=0,
                severity="error",
                summary=(
                    "Internet-facing ALB requires an HTTPS listener on port 443 "
                    "with certificate_arn and a forward action"
                ),
                fix_hint=(
                    'Add an aws_lb_listener on port 443, protocol "HTTPS", with '
                    "ssl_policy, certificate_arn, and a forward default_action"
                ),
            )
        )

    for l in listeners:
        if l.port != 80 or (l.protocol or "").upper() != "HTTP":
            continue
        if l.action_type == "forward":
            violations.append(
                Violation(
                    check="policy",
                    rule="alb_http_redirect",
                    file=l.file,
                    line=l.line,
                    severity="error",
                    summary=(
                        f"ALB HTTP listener '{l.name}' on port 80 forwards to targets; "
                        "it must redirect to HTTPS"
                    ),
                    fix_hint=(
                        "Replace the forward default_action with a redirect block: "
                        'type = "redirect", redirect { port = "443", protocol = "HTTPS", '
                        'status_code = "HTTP_301" }'
                    ),
                )
            )

    return violations


_DB_PORTS = (5432, 3306)

# Well-known admin / datastore ports that should never be open to 0.0.0.0/0.
# Deliberately EXCLUDES 5432/3306 (covered by db_sg_no_public_ingress, so no
# double-reporting) and web ports 80/443 (legitimately public). Kept tight to
# unambiguous "never public" ports so valid designs (e.g. game servers on high
# ports) are not falsely flagged.
_SENSITIVE_NONDB_PORTS = (
    22,     # SSH
    3389,   # RDP
    6379,   # Redis
    11211,  # Memcached
    27017,  # MongoDB
    9200,   # Elasticsearch HTTP
    9300,   # Elasticsearch transport
    5601,   # Kibana
)


def check_rds_not_public(tf_files: list[tuple[str, str]]) -> list[Violation]:
    """Flag RDS resources that explicitly set publicly_accessible = true.

    Fail-open: absent (RDS default is false) or variable-driven values do not
    fire — only a literal `true` is a violation.
    """
    violations: list[Violation] = []
    for rel_path, content in tf_files:
        for res_type in ("aws_db_instance", "aws_rds_cluster"):
            for name, body, line in _extract_blocks(content, res_type):
                if _attr_string(body, "publicly_accessible") == "true":
                    violations.append(
                        Violation(
                            check="policy",
                            rule="rds_not_public",
                            file=rel_path,
                            line=line,
                            severity="error",
                            summary=(
                                f"{res_type} '{name}' sets publicly_accessible = true — "
                                "the database is reachable from the internet"
                            ),
                            fix_hint=(
                                "Set publicly_accessible = false and place the database in "
                                "private subnets; reach it from application security groups only"
                            ),
                        )
                    )
    return violations


def _ingress_covered_ports(ingress_body: str, ports: tuple[int, ...]) -> list[int]:
    """Return the subset of `ports` whose value falls in this ingress rule's
    [from_port, to_port] range. Empty when the range is missing/non-literal."""
    from_p = _attr_int(ingress_body, "from_port")
    to_p = _attr_int(ingress_body, "to_port")
    if from_p is None or to_p is None:
        return []
    return [port for port in ports if from_p <= port <= to_p]


def _ingress_covers_db_port(ingress_body: str) -> bool:
    return bool(_ingress_covered_ports(ingress_body, _DB_PORTS))


def _ingress_allows_public(ingress_body: str) -> bool:
    # Match a cidr_blocks list literal and look for 0.0.0.0/0 inside it.
    m = re.search(r"cidr_blocks\s*=\s*\[(.*?)\]", ingress_body, re.DOTALL)
    if not m:
        return False
    return "0.0.0.0/0" in m.group(1)


def check_db_sg_no_public_ingress(tf_files: list[tuple[str, str]]) -> list[Violation]:
    """Flag inline security-group ingress that opens a DB port to 0.0.0.0/0.

    Fail-open: only INLINE `ingress { ... }` blocks inside aws_security_group are
    inspected. Separate aws_security_group_rule / aws_vpc_security_group_ingress_rule
    resources are not correlated here (this static reader cannot resolve the
    referenced security_group_id), so they never trigger a false positive.
    """
    violations: list[Violation] = []
    for rel_path, content in tf_files:
        for name, body, line in _extract_blocks(content, "aws_security_group"):
            # Walk each inline ingress block via brace matching.
            for m in re.finditer(r"ingress\s*\{", body):
                ingress_body, _ = _extract_braced_block(body, m.end() - 1)
                if _ingress_covers_db_port(ingress_body) and _ingress_allows_public(ingress_body):
                    violations.append(
                        Violation(
                            check="policy",
                            rule="db_sg_no_public_ingress",
                            file=rel_path,
                            line=line,
                            severity="error",
                            summary=(
                                f"aws_security_group '{name}' has an ingress rule that opens a "
                                "database port (5432/3306) to 0.0.0.0/0"
                            ),
                            fix_hint=(
                                "Restrict the ingress to the application security group "
                                "(security_groups = [aws_security_group.app.id]) or a private "
                                "CIDR — never 0.0.0.0/0 for a database port"
                            ),
                        )
                    )
    return violations


def check_sg_no_public_admin_ingress(tf_files: list[tuple[str, str]]) -> list[Violation]:
    """Flag inline security-group ingress that opens a well-known admin/datastore
    port (SSH, RDP, Redis, Memcached, Mongo, Elasticsearch, Kibana) to 0.0.0.0/0.

    Deliberately scoped to a fixed list of ports that are ~never legitimately
    public — NOT "any public ingress" — so valid public workloads (web on
    80/443, game servers on high ports, etc.) are not falsely flagged. DB ports
    (5432/3306) are handled by db_sg_no_public_ingress and excluded here to avoid
    double-reporting.

    Fail-open (same scope as db_sg_no_public_ingress): only INLINE ingress blocks
    inside aws_security_group are inspected; separate rule resources are not
    correlated.
    """
    port_names = {
        22: "SSH", 3389: "RDP", 6379: "Redis", 11211: "Memcached",
        27017: "MongoDB", 9200: "Elasticsearch", 9300: "Elasticsearch",
        5601: "Kibana",
    }
    violations: list[Violation] = []
    for rel_path, content in tf_files:
        for name, body, line in _extract_blocks(content, "aws_security_group"):
            for m in re.finditer(r"ingress\s*\{", body):
                ingress_body, _ = _extract_braced_block(body, m.end() - 1)
                if not _ingress_allows_public(ingress_body):
                    continue
                hit = _ingress_covered_ports(ingress_body, _SENSITIVE_NONDB_PORTS)
                if not hit:
                    continue
                labels = ", ".join(f"{p} ({port_names[p]})" for p in sorted(set(hit)))
                violations.append(
                    Violation(
                        check="policy",
                        rule="sg_no_public_admin_ingress",
                        file=rel_path,
                        line=line,
                        severity="error",
                        summary=(
                            f"aws_security_group '{name}' opens sensitive port(s) {labels} "
                            "to 0.0.0.0/0"
                        ),
                        fix_hint=(
                            "Restrict this ingress to a bastion/app security group or a private "
                            "CIDR; never expose admin or datastore ports to the internet"
                        ),
                    )
                )
    return violations


def _iam_key_is_wildcard(body: str, key: str) -> bool:
    """True if an IAM policy `key` (Action/Resource) is a sole "*" — string OR
    list form. Matches:
        "Action"   : "*"          (heredoc JSON, string)
        Action     = "*"          (jsonencode HCL, string)
        "Resource" : ["*"]        (heredoc JSON, single-element list)
        Resource   = ["*"]        (jsonencode HCL, single-element list)
    A list is only treated as wildcard when "*" is its ONLY element — a list that
    also contains scoped ARNs/actions is not a blanket wildcard.
    """
    # String form: key = "*"
    if re.search(rf'"?{key}"?\s*[:=]\s*"\*"', body):
        return True
    # List form: key = [ "*" ] with nothing else inside the brackets.
    m = re.search(rf'"?{key}"?\s*[:=]\s*\[(.*?)\]', body, re.DOTALL)
    if m:
        inner = m.group(1).strip()
        if inner == '"*"':
            return True
    return False


def check_no_wildcard_iam(tf_files: list[tuple[str, str]]) -> list[Violation]:
    """Flag literal IAM policy JSON with an Allow statement using Action/Resource "*".

    Fail-open: only literal `policy = jsonencode({...})` / heredoc JSON inside
    aws_iam_policy, aws_iam_role_policy, or *_inline_policy blocks is scanned.
    aws_iam_policy_document DATA sources are not inspected (their statements are
    HCL blocks, not literal JSON here) — avoids false positives on the common,
    reviewable data-source pattern. Assume-role trust policies are excluded
    (a Service/AWS principal trust with Action sts:AssumeRole is not a wildcard).
    """
    violations: list[Violation] = []
    policy_res_types = ("aws_iam_policy", "aws_iam_role_policy", "aws_iam_group_policy",
                        "aws_iam_user_policy")
    for rel_path, content in tf_files:
        for res_type in policy_res_types:
            for name, body, line in _extract_blocks(content, res_type):
                # Accept both heredoc JSON ("Effect": "Allow") and HCL jsonencode
                # ({...}) (Effect = "Allow") forms — the separator is : or =.
                if not re.search(r'"?Effect"?\s*[:=]\s*"Allow"', body):
                    continue
                if _iam_key_is_wildcard(body, "Action") or _iam_key_is_wildcard(body, "Resource"):
                    violations.append(
                        Violation(
                            check="policy",
                            rule="no_wildcard_iam",
                            file=rel_path,
                            line=line,
                            severity="error",
                            summary=(
                                f"{res_type} '{name}' grants Action \"*\" or Resource \"*\" "
                                "in an Allow statement — over-broad permissions"
                            ),
                            fix_hint=(
                                "Scope the policy to specific actions and resource ARNs; "
                                "replace \"*\" with the minimal set the workload needs"
                            ),
                        )
                    )
    return violations


def check_rds_encryption_at_rest(tf_files: list[tuple[str, str]]) -> list[Violation]:
    """Flag RDS resources that do not enable storage_encrypted (RDS defaults to
    UNENCRYPTED).

    Fail-open: fires only when storage_encrypted is literally `false` OR the
    attribute is absent. A variable-driven value (storage_encrypted = var.x) is
    NOT flagged. S3 is intentionally excluded — buckets have default SSE-S3 since
    Jan 2023, so a missing SSE block is not an unencrypted bucket.
    """
    violations: list[Violation] = []
    for rel_path, content in tf_files:
        for res_type in ("aws_db_instance", "aws_rds_cluster"):
            for name, body, line in _extract_blocks(content, res_type):
                val = _attr_string(body, "storage_encrypted")
                # Variable-driven / non-literal → attribute present but not "true"/"false".
                has_attr = re.search(r"^\s*storage_encrypted\s*=", body, re.MULTILINE)
                if has_attr and val is None:
                    continue  # variable-driven — fail open
                if val == "true":
                    continue
                violations.append(
                    Violation(
                        check="policy",
                        rule="rds_encryption_at_rest",
                        file=rel_path,
                        line=line,
                        severity="error",
                        summary=(
                            f"{res_type} '{name}' does not set storage_encrypted = true — "
                            "RDS storage defaults to unencrypted"
                        ),
                        fix_hint="Set storage_encrypted = true (optionally with a kms_key_id)",
                    )
                )
    return violations


def check_elasticache_encryption_at_rest(tf_files: list[tuple[str, str]]) -> list[Violation]:
    """Flag ElastiCache replication groups without at-rest encryption enabled.

    Applies to aws_elasticache_replication_group (the resource that supports
    at_rest_encryption_enabled). Fires when the attribute is literally `false` or
    absent; a variable-driven value fails open. aws_elasticache_cluster is NOT
    checked — standalone Memcached clusters don't support this attribute and
    Redis-in-cluster is configured via the replication group.
    """
    violations: list[Violation] = []
    for rel_path, content in tf_files:
        for name, body, line in _extract_blocks(content, "aws_elasticache_replication_group"):
            val = _attr_string(body, "at_rest_encryption_enabled")
            has_attr = re.search(
                r"^\s*at_rest_encryption_enabled\s*=", body, re.MULTILINE
            )
            if has_attr and val is None:
                continue  # variable-driven — fail open
            if val == "true":
                continue
            violations.append(
                Violation(
                    check="policy",
                    rule="elasticache_encryption_at_rest",
                    file=rel_path,
                    line=line,
                    severity="error",
                    summary=(
                        f"aws_elasticache_replication_group '{name}' does not set "
                        "at_rest_encryption_enabled = true"
                    ),
                    fix_hint=(
                        "Set at_rest_encryption_enabled = true (and consider "
                        "transit_encryption_enabled = true for in-transit protection)"
                    ),
                )
            )
    return violations


def validate(terraform_dir: Path) -> tuple[bool, list[Violation]]:
    tf_files = _read_tf_files(terraform_dir)
    if not tf_files:
        # Preserve the existing no_tf_files verdict path.
        return False, check_alb_https_policy(terraform_dir)

    violations: list[Violation] = []
    violations.extend(check_alb_https_policy(terraform_dir))
    violations.extend(check_rds_not_public(tf_files))
    violations.extend(check_db_sg_no_public_ingress(tf_files))
    violations.extend(check_sg_no_public_admin_ingress(tf_files))
    violations.extend(check_no_wildcard_iam(tf_files))
    violations.extend(check_rds_encryption_at_rest(tf_files))
    violations.extend(check_elasticache_encryption_at_rest(tf_files))
    return len(violations) == 0, violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated Terraform policy rules")
    parser.add_argument("terraform_dir", type=Path, help="Path to terraform/ directory")
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional path to write a machine-readable JSON verdict",
    )
    args = parser.parse_args()

    terraform_dir = args.terraform_dir.resolve()
    if not terraform_dir.is_dir():
        print(f"POLICY_FAIL | path={terraform_dir} | reason=not_a_directory", file=sys.stderr)
        return 2

    ok, violations = validate(terraform_dir)

    if args.json is not None:
        report = {
            "check": "policy",
            "policy_status": "POLICY_OK" if ok else "POLICY_FAIL",
            "violations": [asdict(v) for v in violations],
        }
        try:
            args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"POLICY_FAIL | reason=json_write_failed | detail={exc}", file=sys.stderr)
            return 2

    checks = (
        "alb_https,rds_not_public,db_sg_no_public_ingress,sg_no_public_admin_ingress,"
        "no_wildcard_iam,rds_encryption,elasticache_encryption"
    )

    if ok:
        print(f"POLICY_OK | checks={checks}")
        return 0

    print(f"POLICY_FAIL | checks={checks}", file=sys.stderr)
    for v in violations:
        print(
            f"POLICY_FAIL | file={v.file} | line={v.line} | rule={v.rule} | reason={v.summary}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
