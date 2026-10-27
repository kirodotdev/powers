# llm-bedrock-pricing.py
# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3>=1.35,<2", "botocore>=1.35,<2"]
# ///
"""Look up Amazon Bedrock on-demand token prices.

Primary source is the curated STATIC_FALLBACK table below (checked against the
public pricing page). The live AWS Pricing API is tried as a secondary source
for models not in the table — note its 'model' attribute holds display names
("Claude 3 Haiku"), NOT model IDs, so we query with a display name derived
from the model id; this is best-effort and may miss.

Usage: python llm-bedrock-pricing.py --region <r> --models <id,id,...>
Prints JSON {model_id: {input_per_1k_usd, output_per_1k_usd, available, note}}.
Never raises on lookup failure — emits an 'available: false' banner instead.
"""
import argparse, json, re, sys


def parse_price_dimensions(price_item: dict) -> dict:
    """Pure: pull input/output per-1K-token USD rates from one PriceList item.
    Only matches base input/output token dimensions — excludes cache read/write
    and other extended dimensions that share the 'input'/'output' substring."""
    inp = out = None
    terms = price_item.get("terms", {}).get("OnDemand", {})
    for term in terms.values():
        for dim in term.get("priceDimensions", {}).values():
            usd = float(dim.get("pricePerUnit", {}).get("USD", "0") or 0)
            desc = dim.get("description", "").lower()
            if any(skip in desc for skip in ("cache", "read", "write", "batch")):
                continue
            if "input" in desc and "token" in desc:
                inp = usd
            elif "output" in desc and "token" in desc:
                out = usd
    return {"input_per_1k_usd": inp, "output_per_1k_usd": out}


# Static fallback table: per-1K-token USD rates from public pricing pages.
# Used when the PriceList API doesn't return data (e.g. new cross-region inference profile IDs).
# Source: https://aws.amazon.com/bedrock/pricing/ (checked 2026-06)
STATIC_FALLBACK = {
    "anthropic.claude-haiku-4-5-20251001-v1:0":     {"input_per_1k_usd": 0.001, "output_per_1k_usd": 0.005},
    "us.anthropic.claude-haiku-4-5-20251001-v1:0":  {"input_per_1k_usd": 0.001, "output_per_1k_usd": 0.005},
    "anthropic.claude-sonnet-4-6-20250514-v1:0":    {"input_per_1k_usd": 0.003, "output_per_1k_usd": 0.015},
    "us.anthropic.claude-sonnet-4-6-20250514-v1:0": {"input_per_1k_usd": 0.003, "output_per_1k_usd": 0.015},
    "us.anthropic.claude-sonnet-4-6":               {"input_per_1k_usd": 0.003, "output_per_1k_usd": 0.015},
    "anthropic.claude-opus-4-8-20250610-v1:0":      {"input_per_1k_usd": 0.015, "output_per_1k_usd": 0.075},
    "us.anthropic.claude-opus-4-8-20250610-v1:0":   {"input_per_1k_usd": 0.015, "output_per_1k_usd": 0.075},
    "amazon.nova-micro-v1:0":                       {"input_per_1k_usd": 0.000035, "output_per_1k_usd": 0.00014},
    "amazon.nova-lite-v1:0":                        {"input_per_1k_usd": 0.00006, "output_per_1k_usd": 0.00024},
    "amazon.nova-pro-v1:0":                         {"input_per_1k_usd": 0.0008, "output_per_1k_usd": 0.0032},
}


def unavailable(note: str) -> dict:
    return {"available": False, "input_per_1k_usd": None,
            "output_per_1k_usd": None, "note": f"Pricing unavailable: {note}"}


def _static_fallback(model_id: str) -> dict | None:
    """Try the static fallback table. Returns a result dict or None."""
    entry = STATIC_FALLBACK.get(model_id)
    if entry:
        return {**entry, "available": True, "note": "static fallback (PriceList API had no entry)"}
    # Try stripping the version suffix for a partial match (e.g. us.anthropic.claude-sonnet-4-6)
    base = model_id.rsplit("-v", 1)[0] if "-v" in model_id else model_id
    for key, val in STATIC_FALLBACK.items():
        if key.startswith(base):
            return {**val, "available": True, "note": f"static fallback (matched {key})"}
    return None


def display_name_guess(model_id: str) -> str:
    """Pure: derive a Pricing-API display-name guess from a Bedrock model id.
    'us.anthropic.claude-haiku-4-5-20251001-v1:0' -> 'Claude Haiku 4.5'.
    The Pricing API's 'model' attribute holds display names, not model ids."""
    base = model_id.split(":", 1)[0]
    base = re.sub(r"^(us|eu|apac|global)\.", "", base)
    base = base.split(".", 1)[-1]                      # drop vendor prefix
    base = re.sub(r"-v\d+$", "", base)                 # drop -v1
    base = re.sub(r"-\d{8}$", "", base)                # drop date stamp
    words = []
    for tok in base.split("-"):
        if tok.isdigit():
            # version digits join with '.' (4-5 -> 4.5)
            if words and re.match(r"^\d[\d.]*$", words[-1]):
                words[-1] = f"{words[-1]}.{tok}"
            else:
                words.append(tok)
        else:
            words.append(tok.capitalize())
    return " ".join(words)


def lookup(region: str, model_id: str) -> dict:
    # Curated static table is the primary source — the Pricing API keys models
    # by display name and frequently lacks entries for new inference profiles.
    fb = _static_fallback(model_id)
    if fb:
        fb["note"] = "static pricing table (checked 2026-06 against aws.amazon.com/bedrock/pricing)"
        return fb
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    try:
        # Best-effort live lookup for models not in the static table.
        # Pricing API is only served from us-east-1 / ap-south-1.
        client = boto3.client("pricing", region_name="us-east-1")
        resp = client.get_products(
            ServiceCode="AmazonBedrock",
            Filters=[
                {"Type": "TERM_MATCH", "Field": "model", "Value": display_name_guess(model_id)},
                {"Type": "TERM_MATCH", "Field": "regionCode", "Value": region},
            ],
            MaxResults=1,
        )
        items = resp.get("PriceList", [])
        if not items:
            return unavailable(
                f"not in static table and no PriceList entry for display name "
                f"'{display_name_guess(model_id)}' in {region}")
        parsed = parse_price_dimensions(json.loads(items[0]))
        parsed["available"] = parsed["input_per_1k_usd"] is not None
        parsed["note"] = (f"live Pricing API (matched display name '{display_name_guess(model_id)}')"
                          if parsed["available"] else "rates not found in price item")
        return parsed
    except (BotoCoreError, ClientError, ValueError, TypeError, AttributeError) as e:
        return unavailable(str(e))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--models", required=True)
    args = ap.parse_args(argv)
    out = {m.strip(): lookup(args.region, m.strip())
           for m in args.models.split(",") if m.strip()}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
