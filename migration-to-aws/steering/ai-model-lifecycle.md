# Bedrock Model Lifecycle Awareness

Reference: [Amazon Bedrock Model Lifecycle](https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html)

Models on Bedrock move through three states: **Active** → **Legacy** (minimum 6 months before EOL) → **End-of-Life (EOL)**. After EOL, the model is unavailable and requests fail.

For models with EOL dates after February 1, 2026, a **public extended access** period begins at least 3 months into the Legacy state. During this period pricing may increase at the model provider's discretion.

---

## Lifecycle States (Not the Same Thing)

| State      | What it means                                                                                                                                                                                                               | Usable?                |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| **Active** | Provider is actively maintaining the model. Full feature access.                                                                                                                                                            | Yes                    |
| **Legacy** | Deprecated. Still works for existing users, but new Provisioned Throughput cannot be created, new customers cannot onboard, pricing may increase during public extended access, and the model is on a countdown to removal. | Yes, with restrictions |
| **EOL**    | Model is removed. All inference requests fail.                                                                                                                                                                              | **No**                 |

**Legacy does not mean unavailable** — it means the model still functions today but has a firm expiration date. EOL means unavailable.

---

## Selection Rules

### Rule 1: Active models only for new migrations

**New migrations must target Active models only.** Do not recommend a Legacy or EOL model as the primary selection for any new migration, even if it is cheaper.

### Rule 2: 90-day exclusion zone

**Models within 90 days of their EOL date must be excluded from all recommendation and comparison tables.** A migration takes weeks or months to plan, test, and deploy. Recommending a model that will be unavailable before the migration is production-ready is harmful.

- **Excluded** = do not list in "Best Bedrock Match" columns, tiered strategy tables, or `recommended_model` / `backup_model` fields.
- These models may still appear in the pricing cache (for reference by users already on them) but must be marked `excluded (EOL YYYY-MM-DD)` in the Status column.

### Rule 3: Legacy models outside the 90-day zone

Legacy models with >90 days until EOL may appear in comparison tables **with annotation** (`Legacy — EOL YYYY-MM-DD`), but never as `recommended_model` or "Best Bedrock Match" when an Active alternative exists.

### Applying the rules

On each run, compute `days_to_eol = EOL date − today` for every model in the Legacy/EOL table below. Then:

1. `days_to_eol ≤ 0` → EOL. Remove from all tables.
2. `0 < days_to_eol ≤ 90` → **Exclusion zone.** Remove from recommendation/comparison tables. Mark `excluded` in pricing cache.
3. `days_to_eol > 90` and Legacy → Annotate, never recommend as primary.
4. Active → No restrictions.

---

## Legacy / EOL Models (as of June 14, 2026)

Check the [model lifecycle page](https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html) for the authoritative list. The table below captures models referenced elsewhere in this plugin. **Recompute the Status column on each run** using `days_to_eol = EOL date − today`.

| Model                    | Model ID                                    | EOL Date     | Days to EOL | Status       | Active Replacement       |
| ------------------------ | ------------------------------------------- | ------------ | ----------- | ------------ | ------------------------ |
| Titan Image Generator v2 | `amazon.titan-image-generator-v2:0`         | Jun 30, 2026 | 16          | **excluded** | Stability AI (see note)  |
| Llama 3.2 (all sizes)    | `meta.llama3-2-*-instruct-v1:0`             | Jul 7, 2026  | 23          | **excluded** | Llama 4 Scout / Maverick |
| Llama 3.1 405B Instruct  | `meta.llama3-1-405b-instruct-v1:0`          | Jul 7, 2026  | 23          | **excluded** | Llama 4 Maverick         |
| Claude 3 Sonnet          | `anthropic.claude-3-sonnet-20240229-v1:0`   | Jul 30, 2026 | 46          | **excluded** | Claude Sonnet 4.5 / 4.6  |
| Claude 3.5 Sonnet v1     | `anthropic.claude-3-5-sonnet-20240620-v1:0` | Jul 30, 2026 | 46          | **excluded** | Claude Sonnet 4.5 / 4.6  |
| Claude 3.5 Sonnet v2     | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Jul 30, 2026 | 46          | **excluded** | Claude Sonnet 4.5 / 4.6  |
| Command R / R+           | `cohere.command-r-v1:0` / `plus`            | Aug 19, 2026 | 66          | **excluded** | —                        |
| Claude 3 Haiku           | `anthropic.claude-3-haiku-20240307-v1:0`    | Sep 10, 2026 | 88          | **excluded** | Claude Haiku 4.5         |
| Nova Premier v1          | `amazon.nova-premier-v1:0`                  | Sep 14, 2026 | 92          | legacy       | Nova 2 Pro (Preview)     |
| Nova Sonic v1            | `amazon.nova-sonic-v1:0`                    | Sep 14, 2026 | 92          | legacy       | Nova 2 Sonic             |
| Nova Canvas v1           | `amazon.nova-canvas-v1:0`                   | Sep 30, 2026 | 108         | legacy       | Stability AI (see note)  |
| Nova Reel v1             | `amazon.nova-reel-v1:0` / `v1:1`            | Sep 30, 2026 | 108         | legacy       | —                        |
| Claude Sonnet 4          | `anthropic.claude-sonnet-4-20250514-v1:0`   | Oct 14, 2026 | 122         | legacy       | Claude Sonnet 4.5 / 4.6  |
| Jamba 1.5 Large          | `ai21.jamba-1-5-large-v1:0`                 | Nov 26, 2026 | 165         | legacy       | —                        |
| Jamba 1.5 Mini           | `ai21.jamba-1-5-mini-v1:0`                  | Nov 26, 2026 | 165         | legacy       | —                        |

**Status key:** `excluded` = ≤90 days to EOL, must not appear in any recommendation. `legacy` = >90 days to EOL, annotate but do not recommend as primary.

**⚠️ Image generation — Active successor is Stability AI:** Nova Canvas v1 is Legacy (EOL Sep 30, 2026). The Active image generation models on Bedrock are **Stability AI** models:

| Model                      | Model ID                            | Pricing       | Tier     | Use case                              |
| -------------------------- | ----------------------------------- | ------------- | -------- | ------------------------------------- |
| Stable Image Ultra         | `stability.stable-image-ultra-v1:0` | ~$0.08/image  | premium  | Photorealistic, high-end visuals      |
| Stable Diffusion 3.5 Large | `stability.sd3-5-large-v1:0`        | ~$0.065/image | flagship | High volume creative assets           |
| Stable Image Core          | `stability.stable-image-core-v1:0`  | ~$0.04/image  | fast     | Rapid, affordable generation at scale |

When `image_generation` capability is detected:

1. Recommend **Stability AI** models as the primary Active target (not Nova Canvas).
2. Note the pricing model difference: Stability AI charges **per image**, not per token. Direct cost comparison with source provider (DALL-E, Imagen) requires converting to per-image equivalents.
3. If the user's source workload is DALL-E or Imagen, map to Stable Image Ultra (quality-first) or Stable Image Core (cost-first) based on `quality_vs_cost` preference in `preferences.json`.
4. Nova Canvas may appear as a Legacy fallback annotation but must not be `recommended_model`.

---

## Integration Points

### Design Phase (`design-ai.md`)

After selecting a Bedrock model for each workload:

1. Check the Legacy/EOL table above (or the lifecycle page).
2. If the model is in the **exclusion zone** (≤90 days to EOL) or EOL: reject it. Use the Active replacement.
3. If the model is Legacy but >90 days from EOL: replace with Active replacement if one exists. If no Active replacement exists, note the EOL date and recommend the user plan a follow-up migration.
4. If Active: proceed normally.

### Estimate Phase (`estimate-ai.md`)

When building the model comparison table:

- **Exclusion zone models**: omit entirely from `model_comparison`. Do not include in `recommended_model` or `backup_model`.
- **Legacy (>90 days)**: include with `(Legacy — EOL YYYY-MM-DD)` annotation. Never use as `recommended_model` if an Active alternative exists.
- **Active**: no restrictions.

### Pricing Cache (`cached-prices.md`)

The multi-provider quick reference table includes a `Status` column:

| Status value                | Meaning                                                                                 |
| --------------------------- | --------------------------------------------------------------------------------------- |
| `active`                    | No restrictions                                                                         |
| `legacy (EOL YYYY-MM-DD)`   | Legacy, >90 days from EOL. Listed for reference, annotated.                             |
| `excluded (EOL YYYY-MM-DD)` | ≤90 days from EOL. Kept for existing users but must not be selected for new migrations. |

When refreshing the cache, recompute `days_to_eol` and update the Status column from the [model lifecycle page](https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html).

### Mapping Guides (`design-ref-ai-openai-to-bedrock.md`, `design-ref-ai-gemini-to-bedrock.md`)

- "Best Bedrock Match" columns must only contain Active models.
- Exclusion-zone models must not appear in any recommendation row.
- Legacy models (>90 days) may appear in notes or legacy-source mapping rows but never as the primary recommendation.

---

## Refresh Cadence

**On every design run:** The agent MUST recompute `days_to_eol = EOL date − today` for every row in the table above and apply the four rules in "Applying the rules" before making any model recommendation. The static Days to EOL column in this file is a snapshot only — do not use it directly without recomputing.

**Periodic table refresh:** When the table itself needs updating (new models added, EOL dates changed by AWS, or past-EOL rows to remove), update this file and `cached-prices.md` together. The authoritative source is always the [Bedrock model lifecycle page](https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html).

**Past-EOL rows:** Once `days_to_eol ≤ 0`, remove the row from this table entirely on the next periodic refresh — past-EOL models serve no reference value and create confusion.
