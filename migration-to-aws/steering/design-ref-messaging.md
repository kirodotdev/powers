# Messaging Mappings

## google_pubsub_topic

**Purpose:** Pub/Sub message topic for publish-subscribe patterns

**Default:** aws_sns_topic + aws_sqs_queue (SNS+SQS)

**Rationale for default:** SNS+SQS is the most flexible AWS messaging pattern. It supports both fan-out and queuing, covering the full range of Pub/Sub usage patterns.

**Candidates:**
- aws_sns_topic (SNS only)
- aws_sqs_queue (SQS only)
- aws_sns_topic + aws_sqs_queue (SNS+SQS combo)

**Signals:**

| Config Field | Value | Favors | Weight | Reason |
|---|---|---|---|---|
| All subscriptions are push | true | aws_sns_topic | strong | Push delivery aligns with SNS model |
| All subscriptions are pull | true | aws_sqs_queue | strong | Pull/polling aligns with SQS model |
| Mix of push and pull | true | aws_sns_topic + aws_sqs_queue | strong | SNS for fan-out, SQS for pull consumers |
| Multiple subscriptions | true | aws_sns_topic | moderate | Fan-out pattern is SNS's strength |
| Single subscription, pull | true | aws_sqs_queue | strong | No fan-out needed, SQS is simpler |
| Subscription has filter | present | aws_sns_topic | moderate | SNS supports subscription filter policies |

**Eliminators:** None — all candidates work for any Pub/Sub config, they differ in fit.

**Peek at secondaries:** Yes — must look at google_pubsub_subscription resources that serve this topic.

**How to peek:**
1. Find all secondaries where `serves` includes this topic's address
2. Filter to type `google_pubsub_subscription`
3. Check each subscription's config for: push_endpoint (push) vs subscription_type: pull
4. Check for dead_letter_topic, filter, ack_deadline_seconds

**Decision logic:**
1. If all subscriptions have push_endpoint → SNS only
2. If all subscriptions are pull with single subscriber → SQS only
3. If multiple subscribers or mix of push/pull → SNS + SQS
4. If no subscriptions found → default to SNS + SQS

**1:Many Expansion:**

If SNS only:
- aws_sns_topic — primary
- aws_sns_topic_subscription — one per push subscription

If SQS only:
- aws_sqs_queue — primary
- aws_sqs_queue (DLQ) — if dead_letter_topic is configured on any subscription

If SNS + SQS:
- aws_sns_topic — fan-out
- aws_sqs_queue — one per pull subscription
- aws_sns_topic_subscription — to connect SQS queues to SNS topic
- aws_sqs_queue (DLQ) — if dead_letter_topic is configured

**Source Config to Carry Forward:**
- message_retention_duration — determines message retention (SQS: MessageRetentionPeriod, SNS: N/A)
- name — determines resource naming

**Important:** SNS does not support message retention. Messages are delivered immediately and not stored. If message retention is required, use SQS (which supports 1-14 day retention via MessageRetentionPeriod). Do not set message_retention on SNS resources.

**Subscription config to carry forward (from secondaries):**
- ack_deadline_seconds — determines SQS VisibilityTimeout
- message_retention_duration — determines SQS MessageRetentionPeriod
- dead_letter_topic — determines DLQ configuration and maxReceiveCount
- max_delivery_attempts — determines SQS maxReceiveCount on redrive policy
- push_endpoint — determines SNS subscription endpoint
- filter — determines SNS subscription filter policy
- retry_minimum_backoff / retry_maximum_backoff — determines SQS retry behavior

---

## google_pubsub_topic (dead letter)

**Behavior:** A Pub/Sub topic used as a dead letter destination maps differently from a regular topic. It becomes:
- aws_sqs_queue with purpose "dead-letter" if the parent subscription maps to SQS
- aws_sns_topic with purpose "dead-letter" if the parent subscription maps to SNS

Detect by checking if this topic is referenced in any subscription's `dead_letter_topic` field. If so, it does not get its own independent mapping — it's created as part of the parent topic's 1:many expansion.

---

## Secondary: google_pubsub_subscription

**Note:** Subscriptions are classified as secondaries in Pillar 1 but play a special role in Pillar 2. Their config drives the primary topic's mapping decision (push vs pull). After the topic is mapped, subscriptions map as follows:

- If topic mapped to SNS → push subscription becomes aws_sns_topic_subscription
- If topic mapped to SQS → pull subscription is absorbed into SQS config (SQS is inherently pull)
- If topic mapped to SNS+SQS → push subscriptions become SNS subscriptions, pull subscriptions become SQS queues subscribed to SNS

---

## Secondary: google_service_account (pubsub_invoker)

**Behavior:** The pubsub_invoker service account is a GCP-specific pattern for authenticating Pub/Sub push deliveries to Cloud Run. On AWS:
- If using SNS → push to HTTP endpoint, SNS handles delivery natively, no separate identity needed
- If target is Lambda → SNS invokes Lambda directly via aws_lambda_permission, no separate identity
- If target is ECS/App Runner → SNS pushes to HTTPS endpoint, authentication handled differently

This service account typically maps to nothing on AWS. Skip with reason.

---

## google_cloud_tasks_queue

**Purpose:** Task queue for asynchronous HTTP callback execution with rate limiting and retry logic

**Default:** SQS + Lambda (or EventBridge for scheduled tasks)

**Rationale for default:** Cloud Tasks is a rate-limited, retryable task queue — SQS provides equivalent queueing with dead-letter support. EventBridge handles scheduling patterns that Cloud Tasks also supports.

**Candidates:**
- SQS Standard + Lambda — for HTTP callback pattern with retry
- SQS FIFO + Lambda — if ordering matters
- EventBridge + SNS/SQS — for scheduled/delayed task execution

**Signals:**

| Signal | Favors | Weight | Reason |
|---|---|---|---|
| HTTP target tasks (push to URL) | SQS + Lambda | strong | Lambda invoked by SQS, calls target URL |
| Rate limiting configured | SQS + Lambda (with concurrency) | moderate | Lambda reserved concurrency acts as rate limiter |
| Scheduled task execution | EventBridge + SQS | strong | EventBridge handles cron/rate-based scheduling |
| Ordered delivery required | SQS FIFO | strong | FIFO guarantees ordering |

**1:Many Expansion:**
- aws_sqs_queue
- aws_lambda_function (processor)
- aws_lambda_event_source_mapping
- aws_sqs_queue (dead-letter, if retry config present)
