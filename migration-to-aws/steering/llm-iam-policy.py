"""Generate a least-privilege IAM policy for Bedrock model invocation.

Pure module: takes model IDs, region, and account ID — returns a policy dict.
Handles the dual-ARN pattern (foundation-model + inference-profile) required
when cross-region inference profile IDs (us./eu./apac. prefixed) are in use.
"""
import json
import re
import sys

_GEO_PREFIX = re.compile(r"^(us|eu|apac|global)\.")


def is_inference_profile(model_id: str) -> bool:
    """True when the model ID uses a geo-prefix (cross-region inference profile)."""
    return bool(_GEO_PREFIX.match(model_id))


def foundation_model_arn(model_id: str) -> str:
    """ARN for a plain foundation-model ID (no geo prefix)."""
    return f"arn:aws:bedrock:*::foundation-model/{model_id}"


def inference_profile_arn(model_id: str, region: str, account_id: str) -> str:
    """ARN for a cross-region inference profile."""
    return f"arn:aws:bedrock:{region}:{account_id}:inference-profile/{model_id}"


def generate_policy(model_ids: list[str], region: str, account_id: str) -> dict:
    """Build a scoped IAM policy covering exactly the given model IDs.

    Returns a policy dict with one Statement whose Resource list contains:
    - foundation-model ARNs for plain model IDs
    - inference-profile ARNs for geo-prefixed model IDs
    """
    resources = []
    for mid in sorted(set(model_ids)):
        if is_inference_profile(mid):
            resources.append(inference_profile_arn(mid, region, account_id))
            base_id = _GEO_PREFIX.sub("", mid)
            resources.append(foundation_model_arn(base_id))
        else:
            resources.append(foundation_model_arn(mid))

    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockInvokeModelScoped",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                "Resource": sorted(set(resources)),
            }
        ],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate scoped Bedrock IAM policy")
    parser.add_argument("--models", required=True, help="Comma-separated model IDs")
    parser.add_argument("--region", required=True, help="AWS region")
    parser.add_argument("--account-id", required=True, help="AWS account ID")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    model_ids = [m.strip() for m in args.models.split(",") if m.strip()]
    policy = generate_policy(model_ids, args.region, args.account_id)

    output = json.dumps(policy, indent=2) + "\n"
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Policy written to {args.output}", file=sys.stderr)
    else:
        print(output)
