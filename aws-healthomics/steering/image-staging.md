# SOP: Image Staging for Non-PTC Registries

## Purpose

This SOP defines how you, the agent, configure image staging so that HealthOmics workflows can use container images from registries NOT supported by ECR Pull-Through Cache — specifically Seqera Wave, NVIDIA NGC, and Google Artifact Registry. Image staging automatically copies external container images into the customer's ECR at run time and caches them for subsequent runs.

## Trigger Conditions

Follow this SOP WHEN:
- User wants to use containers from Seqera Wave (`community.wave.seqera.io`), NVIDIA NGC (`nvcr.io`), or Google Artifact Registry (`<region>-docker.pkg.dev` — e.g., `us-docker.pkg.dev`, `eu-docker.pkg.dev`, `us-west1-docker.pkg.dev` — or the legacy `gcr.io`).
- User references a container registry that is NOT supported by ECR Pull-Through Cache.
- User asks about image staging or registry staging.

DO NOT follow this SOP WHEN:
- User wants to use containers from Docker Hub, Quay.io, or ECR Public — use the [ECR Pull-Through Cache SOP](./ecr-pull-through-cache.md).
- User already has containers in a private ECR repository — no staging needed.

## Key Concepts

- **Image Staging** — HealthOmics pulls container images from an external registry and pushes them into the customer's ECR before the workflow task runs. Staged images are cached and reused on subsequent runs.
- **Registry Staging Mapping** — A configuration entry mapping an upstream registry URL to an ECR repository prefix with credentials.
- **Resolution Order** — At task launch time: ImageMapping → RegistryMapping (PTC) → Registry Staging Mapping. Staging only triggers for non-PTC registries with a mapping configured.
- **Caching** — First run pulls and pushes to ECR (slower). Subsequent runs find the image in ECR and skip the upstream pull.
- **Staleness Detection** — HealthOmics compares the SHA-256 manifest digest of the staged image against the upstream to detect updates.

## Supported Registries

Each supported registry uses a slightly different secret shape. All three use the field name `accessToken` for the token — the differences are what other fields (if any) are present and what the `username` value must be. **Watch these carefully — a mismatch causes authentication to fail silently at first-run time:**

1. **Seqera secrets contain only `accessToken`** — no `username` (any `username` field is ignored by HealthOmics). NVIDIA and Google secrets contain both `username` and `accessToken`.
2. **NVIDIA and Google require literal `username` values** — `$oauthtoken` (NVIDIA), and either `_json_key` or `oauth2accesstoken` (Google, depending on credential type). Do NOT substitute them with a customer-specific value.
3. **Google Artifact Registry supports two credential types** — a long-lived service-account JSON key (`_json_key`) or a short-lived OAuth 2.0 access token (`oauth2accesstoken`). See the Google Artifact Registry subsection below for both formats.

Under the hood, HealthOmics performs a registry login using Basic Auth `Username:Token`. Each registry's protocol dictates what the username and token need to be; the JSON shape below is what Secrets Manager must store.

Authentication is **required** for all non-PTC registries.

### Seqera Wave — `community.wave.seqera.io`

The secret contains a single field. HealthOmics ignores any `username` field, so do NOT include it — some earlier docs and third-party examples show a `username` alongside the token, but the service reads only `accessToken`.

| Field | Value |
|-------|-------|
| `accessToken` | A Seqera Tower access token |

Secret JSON:
```json
{
  "accessToken": "eyJ..."
}
```

Where to obtain the token: log in at https://seqera.io/wave/, then create a token at https://cloud.seqera.io/tokens.

### NVIDIA NGC — `nvcr.io`

| Field | Value |
|-------|-------|
| `username` | The **literal** string `$oauthtoken` (do not replace with a customer value) |
| `accessToken` | An NGC API key |

Secret JSON:
```json
{
  "username": "$oauthtoken",
  "accessToken": "nvapi-..."
}
```

Where to obtain the API key: log in at https://ngc.nvidia.com/, then generate a key at https://org.ngc.nvidia.com/setup/api-key. NGC treats `$oauthtoken` as the well-known username paired with the API key as the password.

### Google Artifact Registry — `<region>-docker.pkg.dev` (or legacy `gcr.io`)

Common hosts: `us-docker.pkg.dev`, `eu-docker.pkg.dev`, `asia-docker.pkg.dev` (multi-region), or `us-west1-docker.pkg.dev`, `europe-west4-docker.pkg.dev`, `asia-northeast1-docker.pkg.dev`, etc. (single-region). The legacy Container Registry host `gcr.io` also works.

Google Artifact Registry supports **two credential formats**. Both use the `accessToken` field name in the secret; the difference is the `username` value and what goes in `accessToken`. Pick one:

**Option A — Service-account JSON key (long-lived).** Simplest for automation. Google flags this as less secure because the key is long-lived — prefer Option B when the workflow can refresh a short-lived token.

| Field | Value |
|-------|-------|
| `username` | The **literal** string `_json_key` (do not replace with a customer value) |
| `accessToken` | The GCP service-account JSON key, stored as an escaped JSON string in this field |

Secret JSON:
```json
{
  "username": "_json_key",
  "accessToken": "{\"type\":\"service_account\",\"project_id\":\"...\",\"private_key\":\"...\",\"client_email\":\"...\"}"
}
```

Where to obtain: in the GCP project that owns the Artifact Registry, create a service account, grant it the `Artifact Registry Reader` role, then create a JSON key. Paste the entire JSON key object (as an escaped string) into the `accessToken` field.

**Option B — Short-lived OAuth 2.0 access token.** Google's recommended approach. The token is valid for **60 minutes**, so the secret value MUST be refreshed before expiry — this option only fits workflows where an external process rotates the Secrets Manager value on a cadence shorter than 1 hour. If staging pulls the image after the token expires, authentication fails.

| Field | Value |
|-------|-------|
| `username` | The **literal** string `oauth2accesstoken` (do not replace with a customer value) |
| `accessToken` | A short-lived OAuth 2.0 access token (starts with `ya29.`) |

Secret JSON:
```json
{
  "username": "oauth2accesstoken",
  "accessToken": "ya29..."
}
```

Where to obtain the token: generate it for a service account with the `Artifact Registry Reader` role:

```bash
gcloud auth print-access-token \
    --impersonate-service-account SERVICE_ACCOUNT_EMAIL
```

Then write the returned token into the secret's `accessToken` field via `aws secretsmanager put-secret-value` (or `update-secret`). Automate this rotation before the 60-minute TTL elapses.

Reference: https://cloud.google.com/artifact-registry/docs/docker/authentication

## Prerequisites

1. An AWS account with HealthOmics access.
2. Permission to create ECR repositories in the same Region as the workflow.
3. An IAM run role (see Step 1).
4. Credentials from the upstream registry provider.

## Procedure

### Step 1: Create or Verify the IAM Run Role

The run role must allow HealthOmics to assume it (`omics.amazonaws.com` trust policy) and must have:
- **ECR write**: `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer`, `ecr:BatchCheckLayerAvailability`, `ecr:InitiateLayerUpload`, `ecr:UploadLayerPart`, `ecr:CompleteLayerUpload`, `ecr:PutImage`, `ecr:DescribeImages`, `ecr:CreateRepository`, `ecr:GetRepositoryPolicy`, `ecr:SetRepositoryPolicy` on `arn:aws:ecr:*:*:repository/*`
- **ECR auth**: `ecr:GetAuthorizationToken` on `*`
- **Secrets Manager**: `secretsmanager:GetSecretValue` scoped to the secret ARN(s) used as `credentialArn` in the configuration mappings (e.g., `arn:aws:secretsmanager:<region>:<account>:secret:<your-secret-name>-*`). The secret name is chosen by the customer at creation time (Step 2) or by the HealthOmics UI when it auto-creates the secret, so use the actual ARN(s) rather than a fixed prefix.
- **S3**: `s3:GetObject`, `s3:PutObject`, `s3:ListBucket` on `arn:aws:s3:::<output-bucket>` and `arn:aws:s3:::<output-bucket>/*`
- **CloudWatch Logs**: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:DescribeLogStreams`, `logs:PutLogEvents` on `arn:aws:logs:*:*:log-group:/aws/omics/WorkflowLog:*`

### Step 2: Store Registry Credentials in Secrets Manager

Store credentials in the SAME region as the workflow. Use the JSON shape from the per-registry subsection above (Seqera Wave / NVIDIA NGC / Google Artifact Registry) — the field names differ between registries and the literal `username` values (`$oauthtoken`, `_json_key`) must be preserved exactly. The secret name is an arbitrary customer choice — use whatever fits your existing naming conventions. When the HealthOmics UI auto-creates the secret for a registry mapping, it may pick its own name; in that case, use the ARN it returns.

```bash
aws secretsmanager create-secret \
    --name "<your-registry-credentials-secret-name>" \
    --secret-string '<json-from-table-above>' \
    --region <region>
```

Note the secret ARN from the output.

### Step 3: Create the HealthOmics Configuration

Call `CreateAHOConfiguration` with registry staging mappings. Each mapping takes these fields:

| Field | Description |
|-------|-------------|
| `upstreamRegistryUrl` | Registry hostname (e.g., `community.wave.seqera.io`) |
| `ecrRepositoryPrefix` | Prefix for staged ECR repositories |
| `upstreamRepositoryPrefix` | Path prefix in the upstream registry (e.g., `library`) |
| `ecrAccountId` *(optional)* | AWS account ID for ECR repositories |
| `credentialArn` | Secrets Manager ARN with registry credentials |

**Example (Seqera Wave):**
```json
{
  "name": "seqera-wave-image-staging",
  "description": "Image staging for Seqera Wave containers",
  "workflowConfigurations": {
    "stagingConfig": {
      "registryStagingConfiguration": {
        "registryStagingMappings": [
          {
            "upstreamRegistryUrl": "community.wave.seqera.io",
            "ecrRepositoryPrefix": "seqera-wave-staged",
            "upstreamRepositoryPrefix": "library",
            "ecrAccountId": "123456789012",
            "credentialArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:seqera-wave-credentials-AbCdEf"
          }
        ]
      }
    }
  },
  "runConfigurations": {
    "roleArn": "arn:aws:iam::123456789012:role/HealthOmicsStagingRole"
  }
}
```

For **NVIDIA NGC**, replace: `upstreamRegistryUrl` → `nvcr.io`, `upstreamRepositoryPrefix` → `nvidia/clara`, prefix → `nvidia-ngc-staged`.

For **Google Artifact Registry**, replace: `upstreamRegistryUrl` → `us-docker.pkg.dev`, `upstreamRepositoryPrefix` → `<project>/<repo>`, prefix → `google-ar-staged`.

Multiple registries can be combined in one configuration by adding entries to the `registryStagingMappings` array.

### Step 4: Wait for Configuration to Become Active

Call `GetAHOConfiguration` and wait for status `ACTIVE` before starting runs.

### Step 5: Start the Run

Reference the configuration by name. The container image URI can be a workflow parameter or hardcoded in the `runtime` block.

```bash
aws omics start-run \
    --workflow-id <workflow-id> \
    --role-arn arn:aws:iam::123456789012:role/HealthOmicsStagingRole \
    --output-uri s3://my-output-bucket/runs/ \
    --configuration-name seqera-wave-image-staging \
    --parameters '{"runtime_image": "community.wave.seqera.io/library/coreutils_grep_gzip_lbzip2_pruned:838ba80435a629f8"}' \
    --request-id "$(uuidgen)"
```

**What happens:** HealthOmics checks ECR for a cached copy → if absent, authenticates with the upstream registry, pulls the image, pushes to `<account>.dkr.ecr.<region>.amazonaws.com/<prefix>/<path>:<tag>` → runs the task with the staged image.

### Step 6: Verify Results

Check ECR — the staged image appears under `ecrRepositoryPrefix`. Example: `123456789012.dkr.ecr.us-east-1.amazonaws.com/seqera-wave-staged/community.wave.seqera.io/library/coreutils_grep_gzip_lbzip2_pruned:838ba80435a629f8`

## Example WDL Workflow

Pass the container image as a parameter so staging works without modifying the workflow:

```wdl
version 1.0

workflow TestFlow {
    input {
        File input_fasta_file
        String runtime_image
    }
    call ProcessTask { input: input_fasta_file = input_fasta_file, runtime_image = runtime_image }
    output { File result = ProcessTask.output_file }
}

task ProcessTask {
    input {
        File input_fasta_file
        String runtime_image
    }
    runtime { docker: runtime_image }
    command { head -n 1000 ~{input_fasta_file} > outfile.fasta }
    output { File output_file = "outfile.fasta" }
}
```

## Limitations

- **First run is slower** — waits for image staging. Subsequent runs use the cached ECR copy.
- **Authentication required** — HealthOmics rejects staging mappings without a `credentialArn` for non-PTC registries.
- **Same-region** — Secrets Manager secret and ECR must be in the same Region as the workflow.
- **Large images take time** — NVIDIA Parabricks (~30 GB) may take significant time on first use.
- **PTC registries cannot use staging** — HealthOmics rejects staging mappings for PTC-supported registries.
- **Tags and digests supported** — Both `:latest` / `:1.2.3` and `@sha256:...` references work.
- **Concurrent first runs** — If multiple runs reference the same unstaged image, it's staged only once; others wait.
