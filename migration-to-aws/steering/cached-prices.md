# AWS Pricing Cache

**Last updated:** 2026-03-07
**Region:** us-east-1
**Currency:** USD
**Accuracy:** ±5-10% for infrastructure services (sourced from AWS Price List API), ±15-25% for AI models (sourced from public pricing pages)

> Prices may vary by region and change over time. Use for estimation only. For real-time pricing, fall back to the AWS Pricing MCP server.

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

| Metric                        | Rate   |
| ----------------------------- | ------ |
| Log ingestion per GB          | $0.50  |
| Log storage per GB-month      | $0.03  |
| Insights query per GB scanned | $0.005 |
| Custom metric per month       | $0.30  |

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

Prices per 1M tokens. Prompt caching available for Claude models (90% reduction on cached portions). Long Context variants activate automatically when input exceeds 200K tokens — 2x input price, 1.5x output price.

| Model                            | Model ID                                 | Provider  | Input $/1M | Output $/1M | Context | Tier      |
| -------------------------------- | ---------------------------------------- | --------- | ---------- | ----------- | ------- | --------- |
| Claude Sonnet 4.6                | anthropic.claude-sonnet-4-6              | Anthropic | 3.00       | 15.00       | 200K    | flagship  |
| Claude Sonnet 4.6 — Long Context | anthropic.claude-sonnet-4-6              | Anthropic | 6.00       | 22.50       | >200K   | flagship  |
| Claude Opus 4.6                  | anthropic.claude-opus-4-6-v1             | Anthropic | 5.00       | 25.00       | 200K    | premium   |
| Claude Opus 4.6 — Long Context   | anthropic.claude-opus-4-6-v1             | Anthropic | 10.00      | 37.50       | >200K   | premium   |
| Claude Haiku 4.5                 | anthropic.claude-haiku-4-5-20251001-v1:0 | Anthropic | 1.00       | 5.00        | 200K    | fast      |
| Llama 4 Maverick                 | meta.llama4-maverick-17b-instruct-v1:0   | Meta      | 0.24       | 0.97        | 1M      | mid       |
| Llama 4 Scout                    | meta.llama4-scout-17b-instruct-v1:0      | Meta      | 0.17       | 0.66        | 10M     | efficient |
| Llama 3.3 70B                    | meta.llama3-3-70b-instruct-v1:0          | Meta      | 0.72       | 0.72        | 128K    | mid       |
| Llama 3.2 90B                    | meta.llama3-2-90b-instruct-v1:0          | Meta      | 0.72       | 0.72        | 128K    | mid       |
| Nova 2 Lite                      | amazon.nova-2-lite-v1:0                  | Amazon    | 0.33       | 2.75        | 1M      | mid       |
| Nova 2 Pro                       | amazon.nova-2-pro-v1:0                   | Amazon    | 1.38       | 11.00       | 1M      | flagship  |
| Nova Pro                         | amazon.nova-pro-v1:0                     | Amazon    | 0.80       | 3.20        | 300K    | mid       |
| Nova Lite                        | amazon.nova-lite-v1:0                    | Amazon    | 0.06       | 0.24        | 300K    | fast      |
| Nova Micro                       | amazon.nova-micro-v1:0                   | Amazon    | 0.035      | 0.14        | 128K    | budget    |
| Nova Premier                     | amazon.nova-premier-v1:0                 | Amazon    | 2.50       | 12.50       | 1M      | reasoning |
| Mistral Large 3                  | mistral.mistral-large-3-675b-instruct    | Mistral   | 0.50       | 1.50        | 256K    | flagship  |
| DeepSeek-R1                      | deepseek.r1-v1:0                         | DeepSeek  | 1.35       | 5.40        | 128K    | reasoning |
| gpt-oss-20b                      | openai.gpt-oss-20b-1:0                   | OpenAI    | 0.07       | 0.30        | 128K    | budget    |
| gpt-oss-120b                     | openai.gpt-oss-120b-1:0                  | OpenAI    | 0.15       | 0.60        | 128K    | efficient |
| Gemma 3 4B IT                    | google.gemma-3-4b-it                     | Google    | 0.04       | 0.08        | 128K    | budget    |
| Gemma 3 12B IT                   | google.gemma-3-12b-it                    | Google    | 0.09       | 0.29        | 128K    | budget    |
| Gemma 3 27B IT                   | google.gemma-3-27b-it                    | Google    | 0.23       | 0.38        | 128K    | efficient |

---

## Source Provider Pricing (for Migration Comparison)

Use alongside Bedrock pricing to calculate migration ROI.

### Gemini (Standard Tier)

Prices per 1M tokens.

| Model                  | Input $/1M | Output $/1M | Context | Tier     |
| ---------------------- | ---------- | ----------- | ------- | -------- |
| Gemini 3.1 Pro Preview | 2.00       | 12.00       | 1M      | flagship |
| Gemini 2.5 Pro         | 1.25       | 10.00       | 1M      | flagship |
| Gemini 2.5 Flash       | 0.30       | 2.50        | 1M      | fast     |
| Gemini 2.0 Flash       | 0.10       | 0.40        | 1M      | fast     |
| Gemini 2.0 Flash Lite  | 0.075      | 0.30        | 1M      | budget   |

### OpenAI (Standard Tier)

Prices per 1M tokens.

| Model        | Input $/1M | Output $/1M | Context | Tier      |
| ------------ | ---------- | ----------- | ------- | --------- |
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
