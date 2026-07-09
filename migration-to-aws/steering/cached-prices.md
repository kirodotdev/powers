# AWS Pricing Cache

**Last updated:** 2026-06-14
**Region:** us-east-1
**Currency:** USD
**Accuracy:** ±5-10% for infrastructure services (sourced from AWS Price List API), ±15-25% for AI models (sourced from public pricing pages)

> Prices may vary by region and change over time. Use for estimation only. For real-time pricing, fall back to the AWS Pricing MCP server. **Amazon Nova** figures in the Bedrock subsection often reference **US East (Ohio)** and **inference mode** (global vs geo); other services in this file default to **us-east-1** unless noted.
> **Staleness warning:** If today's date is more than 30 days after the **Last updated** date above, treat AI model prices as potentially stale (±15-25% accuracy may widen). Infrastructure prices (Fargate, RDS, S3, etc.) change rarely and remain reliable longer. When staleness is detected, set `pricing_source: "cached_stale"` in the estimate output and note: "Pricing cache is more than 30 days old — AI model prices may have changed. Verify via the AWS Pricing MCP server or [aws.amazon.com/bedrock/pricing](https://aws.amazon.com/bedrock/pricing/)."

---

## Compute

### Fargate

| Metric             | Rate      |
| ------------------ | --------- |
| Per vCPU-hour      | $0.04048  |
| Per GB memory-hour | $0.004445 |

Linux/x86, on-demand.

### Lambda

| Metric                   | Rate                            |
| ------------------------ | ------------------------------- |
| Per request              | $0.0000002                      |
| Per GB-second (first 6B) | $0.0000166667                   |
| Per GB-second (over 6B)  | $0.000015                       |
| Free tier                | 1M requests + 400K GB-sec/month |

### EKS

| Metric                | Rate   |
| --------------------- | ------ |
| Cluster fee per hour  | $0.10  |
| Cluster fee per month | $73.00 |

Worker nodes billed separately as EC2 or Fargate.

### EC2 (On-Demand, Linux)

| Instance  | $/hour | $/month |
| --------- | ------ | ------- |
| t3.micro  | 0.0104 | 7.58    |
| t3.small  | 0.0208 | 15.17   |
| t3.medium | 0.0416 | 30.34   |
| t3.large  | 0.0832 | 60.68   |
| m5.large  | 0.096  | 70.08   |
| m5.xlarge | 0.192  | 140.16  |
| c5.large  | 0.085  | 62.05   |
| c5.xlarge | 0.17   | 124.10  |

---

## Database

### Aurora PostgreSQL (On-Demand)

Aurora replicates across 3 AZs by default. Pricing is listed as Single-AZ — do NOT use Multi-AZ filter with MCP.

| Instance       | $/hour |
| -------------- | ------ |
| db.t4g.medium  | 0.073  |
| db.t4g.large   | 0.146  |
| db.r6g.large   | 0.26   |
| db.r6i.large   | 0.29   |
| db.r7g.xlarge  | 0.553  |
| db.r8g.large   | 0.276  |
| db.r8g.xlarge  | 0.552  |
| db.r8g.2xlarge | 1.104  |
| db.r8g.4xlarge | 2.208  |
| db.r8g.8xlarge | 4.416  |

| Storage/IO               | Rate  |
| ------------------------ | ----- |
| Storage per GB-month     | $0.10 |
| I/O per million requests | $0.20 |

### Aurora MySQL (On-Demand)

Same Multi-AZ note as Aurora PostgreSQL.

| Instance      | $/hour |
| ------------- | ------ |
| db.t4g.medium | 0.073  |
| db.t4g.large  | 0.146  |

Storage and I/O same as Aurora PostgreSQL.

### Aurora Serverless v2

Scales between min and max ACU. Both PostgreSQL and MySQL cost the same per ACU.

| Metric                     | Rate  |
| -------------------------- | ----- |
| Standard per ACU-hour      | $0.12 |
| I/O Optimized per ACU-hour | $0.16 |
| Storage per GB-month       | $0.10 |
| I/O per million requests   | $0.20 |

Min ACU = 0.5, scales to 256 ACU.

### RDS PostgreSQL (On-Demand, Multi-AZ)

| Instance       | $/hour |
| -------------- | ------ |
| db.t4g.micro   | 0.032  |
| db.t4g.small   | 0.065  |
| db.t4g.medium  | 0.129  |
| db.t4g.large   | 0.258  |
| db.t4g.xlarge  | 0.517  |
| db.t4g.2xlarge | 1.034  |

| Storage      | Rate  |
| ------------ | ----- |
| Per GB-month | $0.23 |

### RDS MySQL (On-Demand, Single-AZ)

For Multi-AZ, approximately double these rates.

| Instance      | $/hour | $/month |
| ------------- | ------ | ------- |
| db.t3.small   | 0.034  | 24.82   |
| db.t3.medium  | 0.068  | 49.64   |
| db.t3.large   | 0.136  | 99.28   |
| db.t4g.micro  | 0.016  | 11.68   |
| db.t4g.small  | 0.032  | 23.36   |
| db.t4g.medium | 0.065  | 47.45   |
| db.m5.large   | 0.171  | 124.83  |

| Storage             | Rate   |
| ------------------- | ------ |
| Per GB-month        | $0.23  |
| Backup per GB-month | $0.023 |

### DynamoDB (On-Demand)

| Metric                | Rate   |
| --------------------- | ------ |
| Read per million RRU  | $0.125 |
| Write per million WRU | $0.625 |
| Storage per GB-month  | $0.25  |

### ElastiCache Redis (On-Demand)

Single-AZ pricing. For Multi-AZ, approximately double.

| Node             | $/hour | $/month |
| ---------------- | ------ | ------- |
| cache.t3.micro   | 0.017  | 12.41   |
| cache.t3.small   | 0.034  | 24.82   |
| cache.t3.medium  | 0.068  | 49.64   |
| cache.t4g.micro  | 0.016  | —       |
| cache.t4g.small  | 0.032  | —       |
| cache.t4g.medium | 0.065  | —       |
| cache.r6g.large  | 0.206  | 150.38  |

---

## Storage

### S3

| Tier                       | Rate per GB-month |
| -------------------------- | ----------------- |
| Standard (first 50 TB)     | $0.023            |
| Standard (next 450 TB)     | $0.022            |
| Standard (over 500 TB)     | $0.021            |
| Standard-IA                | $0.0125           |
| Glacier Flexible Retrieval | $0.0036           |

| Requests                 | Rate    |
| ------------------------ | ------- |
| PUT per 1K               | $0.005  |
| GET per 1K               | $0.0004 |
| S3-IA retrieval per GB   | $0.01   |
| Glacier retrieval per GB | $0.01   |

---

## Networking

### Application Load Balancer

| Metric        | Rate    |
| ------------- | ------- |
| Per ALB-hour  | $0.0225 |
| Per LCU-hour  | $0.008  |
| Monthly fixed | $16.43  |

### Network Load Balancer

| Metric        | Rate    |
| ------------- | ------- |
| Per NLB-hour  | $0.0225 |
| Per LCU-hour  | $0.006  |
| Monthly fixed | $16.43  |

### NAT Gateway

| Metric           | Rate   |
| ---------------- | ------ |
| Per hour         | $0.045 |
| Per GB processed | $0.045 |
| Monthly fixed    | $32.85 |

### VPC

VPC itself is free. Add-ons:

| Component                   | Rate   |
| --------------------------- | ------ |
| VPN connection per hour     | $0.05  |
| VPN monthly                 | $36.50 |
| Interface endpoint per hour | $0.01  |
| Interface endpoint monthly  | $7.30  |

### Route 53

| Metric                       | Rate  |
| ---------------------------- | ----- |
| Hosted zone per month        | $0.50 |
| Per million standard queries | $0.40 |
| Per million latency queries  | $0.60 |
| Health check per month       | $0.50 |

### CloudFront (US/Europe)

| Metric                        | Rate                |
| ----------------------------- | ------------------- |
| Per GB transfer (first 10 TB) | $0.085              |
| Per 10K HTTPS requests        | $0.01               |
| Free tier                     | 1 TB transfer/month |

---

## Supporting Services

### Secrets Manager

| Metric               | Rate  |
| -------------------- | ----- |
| Per secret per month | $0.40 |
| Per 10K API calls    | $0.05 |

### CloudWatch

| Metric                                   | Rate   | Notes                                                                            |
| ---------------------------------------- | ------ | -------------------------------------------------------------------------------- |
| Log ingestion per GB (Standard)          | $0.50  |                                                                                  |
| Log ingestion per GB (Infrequent Access) | $0.25  | 50% cheaper than Standard; no Live Tail, subscription filters, or metric filters |
| Log storage per GB-month                 | $0.03  | Same for both Standard and Infrequent Access                                     |
| Insights query per GB scanned            | $0.005 | Same for both log classes                                                        |
| Custom metric per month (≤10K)           | $0.30  | Flat rate at startup scale; $0.10 for 10K–250K, $0.05 for 250K+                  |
| Standard alarm per month                 | $0.10  |                                                                                  |
| High-resolution alarm per month          | $0.30  |                                                                                  |
| Dashboard per month (first 3 free)       | $3.00  |                                                                                  |

Free tier (not subtracted in estimates — startup apps often exceed quickly):

- 5 GB log ingestion + archive + Insights queries
- 10 custom metrics + 10 standard alarms
- 3 dashboards (50 metrics each)

### X-Ray

| Metric                       | Rate  | Notes                 |
| ---------------------------- | ----- | --------------------- |
| Traces recorded per million  | $5.00 | First 100K free/month |
| Traces retrieved per million | $0.50 | First 1M free/month   |
| Traces scanned per million   | $0.50 | First 1M free/month   |

### CloudWatch Container Insights (ECS/Fargate)

| Metric                       | Rate  | Notes                                      |
| ---------------------------- | ----- | ------------------------------------------ |
| Per-task performance log/GB  | $0.50 | Same as standard log ingestion             |
| Cluster/service/task metrics | $0.30 | Per custom metric — can accumulate quickly |

### SQS

| Metric                        | Rate              |
| ----------------------------- | ----------------- |
| Standard per million requests | $0.40             |
| FIFO per million requests     | $0.50             |
| Free tier                     | 1M requests/month |

### SNS

| Metric                    | Rate               |
| ------------------------- | ------------------ |
| Per million publishes     | $0.50              |
| SQS delivery per million  | $0.00              |
| HTTP delivery per million | $0.60              |
| Free tier                 | 1M publishes/month |

### EventBridge

| Metric             | Rate  |
| ------------------ | ----- |
| Per million events | $1.00 |

---

## Analytics

### Redshift Serverless

| Metric               | Rate   |
| -------------------- | ------ |
| Per RPU-hour         | $0.375 |
| Storage per GB-month | $0.024 |

Minimum 8 RPU base capacity.

### Athena

| Metric         | Rate  |
| -------------- | ----- |
| Per TB scanned | $5.00 |

Columnar formats (Parquet, ORC) and partitioning reduce scan volume.

### SageMaker

| Training Instance    | $/hour |
| -------------------- | ------ |
| ml.m5.large          | 0.115  |
| ml.m5.xlarge         | 0.23   |
| ml.g4dn.xlarge (GPU) | 0.736  |

| Inference Instance | $/hour | $/month |
| ------------------ | ------ | ------- |
| ml.t3.medium       | 0.05   | 36.50   |
| ml.m5.large        | 0.115  | 83.95   |

Serverless inference: $0.0000200 per second per GB memory.

---

## Bedrock Models (On-Demand)

**Anthropic Claude (Standard on-demand)** figures below match **US East (N. Virginia)** on [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) as of cache refresh. **Claude Opus 4.7** lists the same headline on-demand input/output as **Opus 4.6** on that page; confirm **batch** availability per model (Opus 4.7 batch was **not** listed on the global cross-region table when this row was added). **Batch**, **prompt cache** (5m / 1h write + cache read), and **geo / in-region cross-region** rows on that page can differ; e.g. **US East (Ohio)** cross-region inference for Claude Sonnet 4.6 is listed at **$3.30 / $16.50** per 1M input/output (≈10% above N. Virginia). Long-context SKUs **do not** all use the same multiplier: **Sonnet 4.6** and **Opus 4.6** long-context modes share the same on-demand rates as the non–long-context rows on the standard table; **Sonnet 4.5** and **Sonnet 4** long-context rows are priced higher on that same table.

### Multi-provider quick reference (per 1M tokens)

See `steering/ai-model-lifecycle.md` for lifecycle details. **Do not recommend Legacy models for new migrations.**

| Model                            | Model ID                                 | Provider  | Input $/1M | Output $/1M | Context | Tier      | Status                     |
| -------------------------------- | ---------------------------------------- | --------- | ---------- | ----------- | ------- | --------- | -------------------------- |
| Claude Sonnet 4.6                | anthropic.claude-sonnet-4-6              | Anthropic | 3.00       | 15.00       | 200K    | flagship  | active                     |
| Claude Sonnet 4.6 — Long Context | anthropic.claude-sonnet-4-6              | Anthropic | 3.00       | 15.00       | 200K+   | flagship  | active                     |
| Claude Opus 4.6                  | anthropic.claude-opus-4-6-v1             | Anthropic | 5.00       | 25.00       | 200K    | premium   | active                     |
| Claude Opus 4.6 — Long Context   | anthropic.claude-opus-4-6-v1             | Anthropic | 5.00       | 25.00       | 200K+   | premium   | active                     |
| Claude Opus 4.5                  | —                                        | Anthropic | 5.00       | 25.00       | 200K    | premium   | active                     |
| Claude Sonnet 4.5                | —                                        | Anthropic | 3.00       | 15.00       | 200K    | flagship  | active                     |
| Claude Sonnet 4.5 — Long Context | —                                        | Anthropic | 6.00       | 22.50       | 200K+   | flagship  | active                     |
| Claude Haiku 4.5                 | anthropic.claude-haiku-4-5-20251001-v1:0 | Anthropic | 1.00       | 5.00        | 200K    | fast      | active                     |
| Claude Sonnet 4                  | anthropic.claude-sonnet-4-20250514-v1:0  | Anthropic | 3.00       | 15.00       | 200K    | flagship  | legacy (EOL Oct 14, 2026)  |
| Llama 4 Maverick                 | meta.llama4-maverick-17b-instruct-v1:0   | Meta      | 0.24       | 0.97        | 1M      | mid       | active                     |
| Llama 4 Scout                    | meta.llama4-scout-17b-instruct-v1:0      | Meta      | 0.17       | 0.66        | 10M     | efficient | active                     |
| Llama 3.3 70B                    | meta.llama3-3-70b-instruct-v1:0          | Meta      | 0.72       | 0.72        | 128K    | mid       | active                     |
| Llama 3.2 90B                    | meta.llama3-2-90b-instruct-v1:0          | Meta      | 0.72       | 0.72        | 128K    | mid       | excluded (EOL Jul 7, 2026) |
| Nova 2 Lite                      | amazon.nova-2-lite-v1:0                  | Amazon    | 0.33       | 2.75        | 1M      | mid       | active                     |
| Nova 2 Pro (Preview)             | amazon.nova-2-pro-v1:0                   | Amazon    | 1.375      | 11.00       | 1M      | flagship  | active                     |
| Nova Pro                         | amazon.nova-pro-v1:0                     | Amazon    | 0.80       | 3.20        | 300K    | mid       | active                     |
| Nova Pro (latency optimized)     | —                                        | Amazon    | 1.00       | 4.00        | 300K    | mid       | active                     |
| Nova Lite                        | amazon.nova-lite-v1:0                    | Amazon    | 0.06       | 0.24        | 300K    | fast      | active                     |
| Nova Micro                       | amazon.nova-micro-v1:0                   | Amazon    | 0.035      | 0.14        | 128K    | budget    | active                     |
| Nova Premier                     | amazon.nova-premier-v1:0                 | Amazon    | 2.50       | 12.50       | 1M      | reasoning | legacy (EOL Sep 14, 2026)  |
| Mistral Large 3                  | mistral.mistral-large-3-675b-instruct    | Mistral   | 0.50       | 1.50        | 256K    | flagship  | active                     |
| DeepSeek-R1                      | deepseek.r1-v1:0                         | DeepSeek  | 1.35       | 5.40        | 128K    | reasoning | active                     |
| DeepSeek-V3.1                    | —                                        | DeepSeek  | 0.58       | 1.68        | —       | mid       | active (Sydney only)       |
| gpt-oss-20b                      | openai.gpt-oss-20b-1:0                   | OpenAI    | 0.07       | 0.30        | 128K    | budget    | active                     |
| gpt-oss-120b                     | openai.gpt-oss-120b-1:0                  | OpenAI    | 0.15       | 0.60        | 128K    | efficient | active                     |
| Gemma 3 4B IT                    | google.gemma-3-4b-it                     | Google    | 0.04       | 0.08        | 128K    | budget    | active                     |
| Gemma 3 12B IT                   | google.gemma-3-12b-it                    | Google    | 0.09       | 0.29        | 128K    | budget    | active                     |
| Gemma 3 27B IT                   | google.gemma-3-27b-it                    | Google    | 0.23       | 0.38        | 128K    | efficient | active                     |
| Jamba 1.5 Large                  | ai21.jamba-1-5-large-v1:0                | AI21 Labs | 2.00       | 8.00        | —       | mid       | legacy (EOL Nov 26, 2026)  |
| Jamba 1.5 Mini                   | ai21.jamba-1-5-mini-v1:0                 | AI21 Labs | 0.20       | 0.40        | —       | efficient | legacy (EOL Nov 26, 2026)  |
| Jurassic-2 Mid                   | —                                        | AI21 Labs | 12.50      | 12.50       | —       | legacy    | legacy                     |
| Jurassic-2 Ultra                 | —                                        | AI21 Labs | 18.80      | 18.80       | —       | legacy    | legacy                     |
| Jamba-Instruct                   | —                                        | AI21 Labs | 0.50       | 0.70        | —       | mid       | active                     |

### Stability AI — Image Generation (per image, US East)

Active image generation models on Bedrock. Priced **per image** (not per token). Use for `image_generation` capability workloads.

| Model                      | Model ID                          | Price/image | Resolution | Tier     | Status |
| -------------------------- | --------------------------------- | ----------- | ---------- | -------- | ------ |
| Stable Image Ultra         | stability.stable-image-ultra-v1:0 | $0.08       | up to 4MP  | premium  | active |
| Stable Diffusion 3.5 Large | stability.sd3-5-large-v1:0        | $0.065      | up to 1MP  | flagship | active |
| Stable Image Core          | stability.stable-image-core-v1:0  | $0.04       | up to 1MP  | fast     | active |

Image editing services (inpaint, erase, upscale, etc.) are priced at $0.03–$0.60/operation. See [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) for full list.

> **Cost comparison note:** DALL-E 3 (OpenAI) charges $0.04–$0.12/image depending on resolution. Google Imagen charges per character of prompt. When comparing, use per-image cost directly — do not convert Stability AI prices to per-token equivalents.

### Anthropic Claude — batch & prompt cache (Standard, US East N. Virginia)

Per 1M tokens unless noted. See [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) for full regional and tier tables.

| Model                    | Batch in | Batch out | 5m cache write | 1h cache write | Cache read |
| ------------------------ | -------- | --------- | -------------- | -------------- | ---------- |
| Claude Sonnet 4.6 (+ LC) | 1.50     | 7.50      | 3.75           | 6.00           | 0.30       |
| Claude Opus 4.6 (+ LC)   | 2.50     | 12.50     | 6.25           | 10.00          | 0.50       |
| Claude Opus 4.5          | 2.50     | 12.50     | 6.25           | 10.00          | 0.50       |
| Claude Haiku 4.5         | 0.50     | 2.50      | 1.25           | 2.00           | 0.10       |
| Claude Sonnet 4.5        | 1.50     | 7.50      | 3.75           | 6.00           | 0.30       |
| Claude Sonnet 4.5 — LC   | 3.00     | 11.25     | 7.50           | 12.00          | 0.60       |

### AI21 Labs

**On-demand**, **US East (N. Virginia)** per [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/). Prices per 1M input / output tokens.

| Model            | Input $/1M | Output $/1M |
| ---------------- | ---------- | ----------- |
| Jamba 1.5 Large  | 2.00       | 8.00        |
| Jamba 1.5 Mini   | 0.20       | 0.40        |
| Jurassic-2 Mid   | 12.50      | 12.50       |
| Jurassic-2 Ultra | 18.80      | 18.80       |
| Jamba-Instruct   | 0.50       | 0.70        |

_Quick-reference rows use **—** for **model ID** and **context**; resolve in the Bedrock console or AWS model documentation._

### Mistral AI

Per [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) (Mistral AI). **Priority** tier ≈ **+75%** vs Standard; **Flex** ≈ **−50%** vs Standard on the same page.

#### US East (Ohio) — Pixtral (on-demand + batch header from page)

| Model                 | Input $/1M | Output $/1M | Batch in | Batch out |
| --------------------- | ---------- | ----------- | -------- | --------- |
| Pixtral Large (25.02) | 2.00       | 6.00        | N/A      | N/A       |

#### On-demand — US East (N. Virginia), US East (Ohio), US West (Oregon)

Prices per 1M input / output tokens.

| Model               | Input $/1M | Output $/1M |
| ------------------- | ---------- | ----------- |
| Devstral 2 123B     | 0.40       | 2.00        |
| Magistral Small 1.2 | 0.50       | 1.50        |
| Voxtral Mini 1.0    | 0.04       | 0.04        |
| Voxtral Small 1.0   | 0.10       | 0.30        |
| Ministral 3B 3.0    | 0.10       | 0.10        |
| Ministral 8B 3.0    | 0.15       | 0.15        |
| Ministral 14B 3.0   | 0.20       | 0.20        |
| Mistral Large 3     | 0.50       | 1.50        |

_Rates differ in **Asia Pacific (Mumbai)**, **São Paulo**, **Tokyo**, **Europe (Ireland/Milan/London)**, **Sydney**, **Jakarta**, **Frankfurt**, **Stockholm** (e.g. Mistral Large 3 Mumbai **$0.59 / $1.76**). **Devstral 2 123B** appears in Jakarta / Frankfurt / Stockholm at **$0.48 / $2.40** on the same page._

### DeepSeek (Amazon Bedrock)

Per [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) (DeepSeek).

#### US East (Ohio) — Standard tier

> **Note:** DeepSeek-V3.1 is no longer listed for US East regions on the Bedrock pricing page as of May 2026. Use DeepSeek-V3.2 for US East deployments. DeepSeek-V3.1 remains available in Asia Pacific (Sydney).

| Model       | Input $/1M | Output $/1M |
| ----------- | ---------- | ----------- |
| DeepSeek-R1 | 1.35       | 5.40        |

#### US East (N. Virginia), US East (Ohio), US West (Oregon)

| Model         | Input $/1M | Output $/1M |
| ------------- | ---------- | ----------- |
| DeepSeek v3.2 | 0.62       | 1.85        |

#### Other regions (examples on same page)

- **Asia Pacific (Mumbai)**, **São Paulo**, **Jakarta**, **Tokyo**, **Stockholm**: DeepSeek v3.2 **$0.74 / $2.22** per 1M.
- **Asia Pacific (Sydney)**: DeepSeek v3.1 **$0.5974 / $1.7304**; v3.2 **$0.6386 / $1.9055** (and **Priority** / **Flex** tiers listed separately on the page).

### OpenAI on Bedrock (gpt-oss)

**Standard tier** per [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) (OpenAI).

| Model        | Region                | Input $/1M | Output $/1M |
| ------------ | --------------------- | ---------- | ----------- |
| gpt-oss-20b  | US East (Ohio)        | 0.07       | 0.30        |
| gpt-oss-120b | US East (Ohio)        | 0.15       | 0.60        |
| gpt-oss-20b  | Asia Pacific (Sydney) | 0.0721     | 0.3090      |
| gpt-oss-120b | Asia Pacific (Sydney) | 0.1545     | 0.6180      |

_The Bedrock page also lists **Flex**, **Priority**, **Batch**, **GPT OSS Safeguard**, and **model customization** pricing for other regions._

### Meta Llama (Amazon Bedrock)

Per [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) (Meta). Prices per 1M input / output tokens unless noted.

#### Llama 4 — US East (Ohio), on-demand and batch

| Model                | On-demand in | On-demand out | Batch in | Batch out |
| -------------------- | ------------ | ------------- | -------- | --------- |
| Llama 4 Maverick 17B | 0.24         | 0.97          | 0.12     | 0.485     |
| Llama 4 Scout 17B    | 0.17         | 0.66          | 0.085    | 0.33      |

#### Llama 3.3 — US East (Ohio), on-demand and batch

| Model                    | On-demand in | On-demand out | Batch in | Batch out |
| ------------------------ | ------------ | ------------- | -------- | --------- |
| Llama 3.3 Instruct (70B) | 0.72         | 0.72          | 0.36     | 0.36      |

#### Llama 3.2 — US East (Ohio), on-demand and batch

> **Lifecycle note:** All Llama 3.2 Instruct models are in the **exclusion zone** (EOL Jul 7, 2026, ≤90 days). Do not select for new migrations. Use **Llama 4 Scout / Maverick** instead. See `steering/ai-model-lifecycle.md`.

| Model                    | On-demand in | On-demand out | Batch in | Batch out |
| ------------------------ | ------------ | ------------- | -------- | --------- |
| Llama 3.2 Instruct (1B)  | 0.10         | 0.10          | N/A      | N/A       |
| Llama 3.2 Instruct (3B)  | 0.15         | 0.15          | N/A      | N/A       |
| Llama 3.2 Instruct (11B) | 0.16         | 0.16          | N/A      | N/A       |
| Llama 3.2 Instruct (90B) | 0.72         | 0.72          | N/A      | N/A       |

#### Llama 3.2 — customization & provisioned throughput (US West Oregon)

**Fine-tuning** (per 1M tokens trained / month storage / no-commit PT per model unit-hour):

| Model                    | Train 1M tokens | Store / month | Infer / unit-hr (no commit) |
| ------------------------ | --------------- | ------------- | --------------------------- |
| Llama 3.2 Instruct (1B)  | $0.50           | $1.95         | $23.00                      |
| Llama 3.2 Instruct (3B)  | $1.10           | $1.95         | $23.00                      |
| Llama 3.2 Instruct (11B) | $3.50           | $1.95         | $23.00                      |
| Llama 3.2 Instruct (90B) | $7.90           | $1.95         | $30.00                      |

**Provisioned throughput** ($/hour per model unit):

| Model                    | No commit | 1-mo commit | 6-mo commit |
| ------------------------ | --------- | ----------- | ----------- |
| Llama 3.2 Instruct (1B)  | $23.00    | $20.30      | $12.54      |
| Llama 3.2 Instruct (3B)  | $23.00    | $20.30      | $12.54      |
| Llama 3.2 Instruct (11B) | $23.00    | $20.30      | $12.54      |
| Llama 3.2 Instruct (90B) | $30.00    | $26.48      | $16.35      |

#### Llama 3.1 — US East (Ohio), on-demand and batch

> **Lifecycle note:** Llama 3.1 405B Instruct is in the **exclusion zone** (EOL Jul 7, 2026, ≤90 days). Do not select for new migrations. Use **Llama 4 Maverick** instead. See `steering/ai-model-lifecycle.md`.

| Model                                              | On-demand in | On-demand out | Batch in | Batch out |
| -------------------------------------------------- | ------------ | ------------- | -------- | --------- |
| Llama 3.1 Instruct (8B)                            | 0.22         | 0.22          | 0.11     | 0.11      |
| Llama 3.1 Instruct (70B)                           | 0.72         | 0.72          | 0.36     | 0.36      |
| Llama 3.1 Instruct (405B)                          | 2.40         | 2.40          | 1.20     | 1.20      |
| Llama 3.1 Instruct (70B) (latency optimized inf.)  | 0.90         | 0.90          | N/A      | N/A       |
| Llama 3.1 Instruct (405B) (latency optimized inf.) | 3.00         | 3.00          | N/A      | N/A       |

#### Llama 3.1 — customization & provisioned throughput (US West Oregon)

| Model                    | Train 1M tokens | Store / month | Infer / unit-hr (no commit) |
| ------------------------ | --------------- | ------------- | --------------------------- |
| Llama 3.1 Instruct (8B)  | $1.49           | $1.95         | $24.00                      |
| Llama 3.1 Instruct (70B) | $7.99           | $1.95         | $24.00                      |

| Model                    | No commit | 1-mo commit | 6-mo commit |
| ------------------------ | --------- | ----------- | ----------- |
| Llama 3.1 Instruct (8B)  | $24.00    | $21.18      | $13.08      |
| Llama 3.1 Instruct (70B) | $24.00    | $21.18      | $13.08      |

#### Llama 3 — US East (N. Virginia), on-demand

| Model                  | Input $/1M | Output $/1M |
| ---------------------- | ---------- | ----------- |
| Llama 3 Instruct (8B)  | 0.30       | 0.60        |
| Llama 3 Instruct (70B) | 2.65       | 3.50        |

#### Llama 2 — US East (N. Virginia) and US West (Oregon), on-demand

| Model              | Input $/1M | Output $/1M |
| ------------------ | ---------- | ----------- |
| Llama 2 Chat (13B) | 0.75       | 1.00        |
| Llama 2 Chat (70B) | 1.95       | 2.56        |

#### Llama 2 — customization & provisioned throughput

**Fine-tuning:** Llama 2 Pretrained (13B) **$1.49** per 1M tokens trained, **$1.95**/month storage, **$23.50**/unit-hr no-commit infer; (70B) **$7.99** / **$1.95** / **$23.50**.

**Provisioned throughput** (per model unit-hour): 13B and 70B — **$21.18** (1-mo commit), **$13.08** (6-mo commit). Pretrained Llama 2 is **provisioned throughput only after customization** per AWS.

### Amazon Nova

All figures from [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) (Amazon Nova sections). Nova pricing depends on **inference deployment** (e.g. **Global cross-region** vs **Geo cross-region and in-region**), **tier** (Standard, Priority, Flex, Batch), **modality** (text / image / video / audio), and **AWS Region**. The quick-reference table above uses **Geo cross-region inference and in-region**, **Standard tier**, **US East (Ohio)**, **text + image + video** rates where a single input price applies to all three. Confirm the page before estimates.

**Cache read (Nova):** AWS states cache read input tokens are **75% below** the on-demand input price for the applicable tier/modality.

#### US East (Ohio) — Standard tier, text + image + video (Geo cross-region inference and in-region)

Per 1M input / output tokens unless noted.

| Model                                    | Input $/1M | Output $/1M |
| ---------------------------------------- | ---------- | ----------- |
| Amazon Nova 2 Lite                       | 0.33       | 2.75        |
| Amazon Nova Micro                        | 0.035      | 0.14        |
| Amazon Nova Lite                         | 0.06       | 0.24        |
| Amazon Nova Pro                          | 0.80       | 3.20        |
| Amazon Nova Pro (latency optimized inf.) | 1.00       | 4.00        |
| Amazon Nova Premier                      | 2.50       | 12.50       |

#### US East (Ohio) — Standard tier, Global cross-region inference (text + image + video)

| Model              | Input $/1M | Output $/1M |
| ------------------ | ---------- | ----------- |
| Amazon Nova 2 Lite | 0.30       | 2.50        |

#### US East (Ohio) — Standard tier, text / image / video / audio (Geo cross-region and in-region)

Per 1M tokens. **Nova 2 Omni** and **Nova 2 Pro** are **Preview**. Image column is **output** image pricing where listed.

| Model                        | Text in | Image in | Video in | Audio in | Text out | Image out |
| ---------------------------- | ------- | -------- | -------- | -------- | -------- | --------- |
| Amazon Nova 2 Omni (Preview) | 0.30    | 0.30     | 0.30     | 1.10     | 2.80     | 44.00     |
| Amazon Nova 2 Pro (Preview)  | 1.375   | 1.375    | 1.375    | 1.375    | 11.00    | N/A       |

**Global cross-region inference (Ohio), Standard** uses different multimodal numbers on the same page — e.g. **Nova 2 Omni (Preview)** audio in **$1.00**, text out **$2.50**, image out **$40.00** (text/image/video in **$0.30** each). Use the Bedrock pricing page for the deployment you select.

#### US East (Ohio) — Nova 2 Lite by tier (text + image + video)

##### Global cross-region inference

| Tier     | Input $/1M | Output $/1M |
| -------- | ---------- | ----------- |
| Standard | 0.30       | 2.50        |
| Priority | 0.525      | 4.375       |
| Flex     | 0.15       | 1.25        |
| Batch    | 0.15       | 1.25        |

##### Geo cross-region inference and in-region

| Tier     | Input $/1M | Output $/1M |
| -------- | ---------- | ----------- |
| Standard | 0.33       | 2.75        |
| Priority | 0.5775     | 4.8125      |
| Flex     | 0.165      | 1.375       |
| Batch    | 0.1595     | 1.342       |

#### US East (Ohio) — Batch tier (text + image + video), selected models

| Model               | Input $/1M | Output $/1M |
| ------------------- | ---------- | ----------- |
| Amazon Nova 2 Lite  | 0.1595     | 1.342       |
| Amazon Nova Micro   | 0.0175     | 0.07        |
| Amazon Nova Lite    | 0.03       | 0.12        |
| Amazon Nova Pro     | 0.40       | 1.60        |
| Amazon Nova Premier | 1.25       | 6.25        |

#### On-demand inference (listed rates, cache read column)

| Model                | Input $/1M | Cache read $/1M | Output $/1M |
| -------------------- | ---------- | --------------- | ----------- |
| Amazon Nova 2.0 Lite | N/A        | N/A             | N/A         |
| Amazon Nova Micro    | 0.035      | N/A             | 0.14        |
| Amazon Nova Lite     | 0.06       | N/A             | 0.24        |
| Amazon Nova Pro      | 0.80       | N/A             | 3.20        |

#### Built-in tools — Web grounding (US East Ohio)

| Model                        | Price                  |
| ---------------------------- | ---------------------- |
| Amazon Nova 2 Omni (Preview) | $30.00 per 1K requests |
| Amazon Nova 2 Pro (Preview)  | $30.00 per 1K requests |
| Amazon Nova Premier          | $30.00 per 1K requests |

#### Creative — US East (N. Virginia)

> **Lifecycle note:** Nova Canvas v1 is **Legacy** (EOL Sep 30, 2026) and Nova Reel v1 is **Legacy** (EOL Sep 30, 2026). Do not recommend for new migrations. See `steering/ai-model-lifecycle.md`.

**Amazon Nova Canvas** (on-demand, per image): up to **1024×1024** — Standard **$0.04**, Premium **$0.06**; up to **2048×2048** — Standard **$0.06**, Premium **$0.08**.

**Model customization (Nova Canvas):** **$0.005** per image seen; **$1.95**/month per custom model stored; provisioned inference per model unit per hour (no commit / 1-mo / 6-mo) **$60.50 / $55.00 / $30.25**.

**Amazon Nova Reel** (video): **720p, 24 fps** — **$0.08** per second of video generated.

#### Speech — US East (N. Virginia)

> **Lifecycle note:** Nova Sonic v1 is **Legacy** (EOL Sep 14, 2026). Prefer **Nova 2 Sonic** for new migrations. See `steering/ai-model-lifecycle.md`.

Per 1M tokens.

| Model               | Modality | Input $/1M | Output $/1M | Status                    |
| ------------------- | -------- | ---------- | ----------- | ------------------------- |
| Amazon Nova Sonic   | Speech   | 3.40       | 13.60       | legacy (EOL Sep 14, 2026) |
| Amazon Nova Sonic   | Text     | 0.06       | 0.24        | legacy (EOL Sep 14, 2026) |
| Amazon Nova 2 Sonic | Speech   | 3.00       | 12.00       | active                    |
| Amazon Nova 2 Sonic | Text     | 0.33       | 2.75        | active                    |

#### Multimodal embeddings — US East (N. Virginia)

| Offering                                      | Text $/1M | Std image / doc image / video sec / audio sec    |
| --------------------------------------------- | --------- | ------------------------------------------------ |
| Amazon Nova Multimodal Embeddings (On-demand) | 0.135     | $0.00006 / $0.0006 / $0.0007 / $0.00014 per unit |
| Amazon Nova Multimodal Embeddings (Batch)     | 0.0675    | $0.00003 / $0.00048 / $0.00056 / $0.000112       |

_On-demand inference for **custom Nova** models matches **base Nova** inference pricing per AWS._

---

## Source Provider Pricing (for Migration Comparison)

Use alongside Bedrock pricing to calculate migration ROI.

### Gemini (Standard Tier)

Prices per 1M tokens. Source: [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing), verified May 2026.

| Model                 | Input $/1M | Output $/1M | Context | Tier     |
| --------------------- | ---------- | ----------- | ------- | -------- |
| Gemini 3.5 Flash      | 1.50       | 9.00        | 1M      | flagship |
| Gemini 3.1 Pro        | 2.00       | 12.00       | 1M      | flagship |
| Gemini 3.1 Flash-Lite | 0.25       | 1.50        | 1M      | budget   |
| Gemini 2.5 Pro        | 1.25       | 10.00       | 1M      | flagship |
| Gemini 2.5 Flash      | 0.30       | 2.50        | 1M      | fast     |
| Gemini 2.0 Flash      | 0.10       | 0.40        | 1M      | fast     |
| Gemini 2.0 Flash Lite | 0.075      | 0.30        | 1M      | budget   |

> **Gemini 3.1 Pro breakpoint pricing:** $4.00/$18.00 per 1M for prompts >200k tokens (vs $2.00/$12.00 for ≤200k). Table above uses ≤200k rates.
> **Gemini 3.5 Flash** is now GA and the current flagship Flash model, replacing Gemini 2.5 Flash as the primary Flash-tier recommendation. At $1.50/$9.00 it is 5x more expensive than Gemini 2.5 Flash — the Bedrock cost savings case is significantly stronger against 3.5 Flash.

### OpenAI (Standard Tier)

Prices per 1M tokens. GPT-5.5 and GPT-5.5 Pro use the same breakpoint pricing structure as GPT-5.4 at 272K input tokens. GPT-5.4 and GPT-5.4 Pro use **breakpoint pricing** at 272K input tokens: rates below are for <272K context; above 272K, input is 2x and output is 1.5x.

| Model        | Input $/1M | Output $/1M | Context | Tier      |
| ------------ | ---------- | ----------- | ------- | --------- |
| GPT-5.5      | 5.00       | 30.00       | 1M      | flagship  |
| GPT-5.5 Pro  | 30.00      | 180.00      | 1M      | premium   |
| GPT-5.4      | 2.50       | 15.00       | 1.05M   | flagship  |
| GPT-5.4 Mini | 0.75       | 4.50        | —       | fast      |
| GPT-5.4 Nano | 0.20       | 1.25        | —       | budget    |
| GPT-5.4 Pro  | 30.00      | 180.00      | 1.05M   | premium   |
| GPT-5.2      | 1.75       | 14.00       | 200K    | flagship  |
| GPT-5.1      | 1.25       | 10.00       | 200K    | flagship  |
| GPT-5 Mini   | 0.25       | 2.00        | 200K    | fast      |
| GPT-5 Nano   | 0.05       | 0.40        | 128K    | budget    |
| GPT-4.1      | 2.00       | 8.00        | 1M      | flagship  |
| GPT-4.1 Mini | 0.40       | 1.60        | 1M      | fast      |
| GPT-4.1 Nano | 0.10       | 0.40        | 1M      | budget    |
| GPT-4o       | 2.50       | 10.00       | 128K    | flagship  |
| o3           | 2.00       | 8.00        | 200K    | reasoning |
| o4-mini      | 1.10       | 4.40        | 200K    | reasoning |

## Security Baseline

**Per-unit rates verified via AWS Pricing API for us-east-1 on 2026-05-04.**
**Config pricing effective 2025-09-01; Security Hub pricing effective 2026-03-01.**
**Re-verify if migrating to a non-us-east-1 region or if any of these services re-prices.**

### CloudTrail

| Metric                                          | Rate                                       |
| ----------------------------------------------- | ------------------------------------------ |
| Management events (first trail per region/type) | $0.00                                      |
| Management events (additional trails)           | $2.00 per 100K events                      |
| Data events                                     | $0.10 per 100K events (not used by Tier 1) |

### GuardDuty

| Metric                      | Rate                       | Notes                                           |
| --------------------------- | -------------------------- | ----------------------------------------------- |
| First 30 days               | $0.00                      | Free trial per account                          |
| CloudTrail event analysis   | $4.00 per 1M events        | First 500M/mo; scales down thereafter           |
| VPC Flow Log / DNS analysis | $1.00 per GB               | First 500 GB/mo                                 |
| DNS query analysis          | $1.00 per 1M queries       |                                                 |
| Small-startup typical       | ~$2–25/mo (typical $14/mo) | After free trial, with ~2M CloudTrail events/mo |

### AWS Config (pricing effective 2025-09-01)

| Metric                             | Rate                                   | Notes                                                                  |
| ---------------------------------- | -------------------------------------- | ---------------------------------------------------------------------- |
| Continuous configuration item      | $0.003 per item                        | Records every change                                                   |
| Daily configuration item           | $0.012 per daily item                  | Once-per-day snapshot; cheaper for slow-changing accounts, less signal |
| Small-startup typical (continuous) | ~$2–10/mo                              | 50–300 CIs/mo continuous                                               |
| Source                             | AWS Pricing API, us-east-1, 2026-05-04 |                                                                        |

### AWS Security Hub (pricing effective 2026-03-01)

| Metric                         | Rate                                   | Notes                                                                |
| ------------------------------ | -------------------------------------- | -------------------------------------------------------------------- |
| First 30 days                  | $0.00                                  | Free trial per account                                               |
| Security checks                | $0.001 per check                       | First 100K checks/mo; tapers above                                   |
| Per-EC2-hour monitoring        | $0.0052083/hr                          | ~$3.80/mo per instance                                               |
| Per-Lambda-function monitoring | $0.000434/hr                           | ~$0.32/mo per function                                               |
| Per-container-image scanning   | $0.0002894/hr                          |                                                                      |
| Small-startup typical          | ~$1–15/mo                              | After trial; Fargate-only startups pay nothing for the EC2 dimension |
| Source                         | AWS Pricing API, us-east-1, 2026-05-04 |                                                                      |

### AWS Budgets

| Metric                      | Rate                     | Notes                                      |
| --------------------------- | ------------------------ | ------------------------------------------ |
| First 2 budgets per account | $0.00                    | Free tier                                  |
| Additional budgets          | $0.02 per budget per day | Tier 1 emits 1 budget, so effectively free |
