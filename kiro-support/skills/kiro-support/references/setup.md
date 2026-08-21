# Setup

How this power reaches the AWS Support API, onboarding, and fixing common failures.

---

## Backends

| Backend | Server key | How it works | Default |
| --- | --- | --- | --- |
| **Primary** | `awslabs.aws-support-mcp-server` | Typed MCP tools | enabled |
| **Fallback** | `aws-mcp` | `aws support …` CLI via toolkit | disabled |

Both use the **same IAM permissions** (`support:*`) and require Business+ support plan.

### When to fall back

| Failure | Action |
| --- | --- |
| Server won't start / not connected / blocked | **Fall back** to toolkit |
| `AccessDenied` | **Don't fall back** → Admin Setup below |
| `SubscriptionRequiredException` | **Don't fall back** → account needs Business+ |

To enable fallback: set `"disabled": false` on `aws-mcp` in `mcp.json`, set same `AWS_PROFILE`, reconnect.

---

## Prerequisites

- **Support plan:** Business, Enterprise On-Ramp, or Enterprise.
- **IAM:** `support:*` via `AWSSupportAccess` managed policy or custom policy below.
- **`uvx`** installed ([install guide](https://docs.astral.sh/uv/getting-started/installation/)).
- **Python 3.10+** for the dedicated server.

---

## Onboarding

### Admin (one-time, ~15 min)

1. Create SSO Permission Set with Support API access (Option A or B below).
2. Assign to Kiro developer group on the account with the Kiro subscription.
3. Confirm account is on Business+ support.
4. Share: SSO start URL, account ID, permission set name.

### Developer

**One-time setup:**

1. `aws configure sso` — use SSO URL and account from admin.
2. Set `AWS_PROFILE` and `AWS_REGION` in this power's `mcp.json`, reconnect server.

**Per-session (recurs):**

3. `aws sso login --profile <profile>` — SSO tokens expire, so re-run when the session lapses (typically daily).
4. Verify: "List my open Kiro support cases." Empty list = success.

---

## Admin Setup

When probe returns `AccessDenied`, the user needs this grant. Offer to draft the admin request.

### Option A — Managed policy (simple)

Attach `AWSSupportAccess` (`arn:aws:iam::aws:policy/AWSSupportAccess`). Grants `support:*` + `support-console:*`.

### Option B — Custom least-privilege (recommended)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowKiroSupportCaseManagement",
    "Effect": "Allow",
    "Action": [
      "support:CreateCase",
      "support:DescribeCases",
      "support:DescribeCommunications",
      "support:AddCommunicationToCase",
      "support:AddAttachmentsToSet",
      "support:DescribeAttachment",
      "support:DescribeServices",
      "support:DescribeSeverityLevels",
      "support:DescribeCreateCaseOptions",
      "support:DescribeSupportedLanguages",
      "support:ResolveCase"
    ],
    "Resource": "*"
  }]
}
```

`Resource: "*"` is expected — Support actions don't support resource-level scoping.

---

## MCP Config

Both servers ship with `AWS_PROFILE` placeholder — **no default**. User must set it before filing.

- Set `AWS_PROFILE` to their profile name in `mcp.json`.
- `AWS_REGION` should be `us-east-1` (Support API global endpoint).
- Reconnect server after editing.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `SubscriptionRequiredException` | Account not on Business+. Route to admin. |
| `AccessDenied` | Missing `support:*`. Use Admin Setup above. |
| Server won't start | Check `uvx --version`, `uv python install 3.10`, valid `AWS_PROFILE`. |
| "Server not connected" | Retry once (init delay). If persistent: `aws sso login`, reconnect. |
| `InvalidParameterValueException` | Invalid code combo. Re-run `describe_create_case_options`. |
| "unexpected keyword argument" | Using camelCase. Switch to `snake_case`. |
| `ExpiredTokenException` | `aws sso login --profile <profile>`, reconnect. |
| `CaseIdNotFound` | Wrong account or invalid ID. Run `describe_support_cases` to list valid IDs. |
| Toolkit `AccessDenied` | Profile lacks `support:*`. Same fix as dedicated server. |
| Toolkit wrong region | Pass `--region us-east-1` on every command. |
