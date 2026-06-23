"""Agent 2: Financial Extractor — pulls structured CRE metrics from parsed PDF text."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


SYSTEM_PROMPT = """You are a commercial real estate financial analyst AI. Your job is to extract specific financial and property data from offering memorandum (OM) text.

CRITICAL RULES:
1. NEVER invent or estimate numbers that are not explicitly stated in the text.
2. Every extracted value MUST cite the page number where it was found.
3. If a value is not found anywhere in the document, set value=null, confidence=0, flag="missing".
4. Confidence score (0-100) reflects how clearly the value was stated, NOT how likely it exists.
   - 90-100: Explicitly labeled and unambiguous
   - 70-89: Stated but requires minor inference (e.g., totaling units from a rent roll)
   - 50-69: Implied or partially stated
   - 0-49: Not found or very unclear

Return ONLY a valid JSON object — no explanation, no markdown fences."""

EXTRACTION_PROMPT = """Extract the following fields from this offering memorandum text. Return a single JSON object where each key maps to an object with:
  - "value": the extracted value (number, string, or null)
  - "confidence": integer 0-100
  - "source_page": page number where found (integer or null)
  - "flag": null if found, "missing" if not found

Fields to extract:
- property_name: string, the name or address of the property
- location: string, city/state/market
- asset_class: string, e.g. "Multifamily", "Office", "Retail", "Industrial", "Mixed-Use"
- units: integer, number of units/doors (for multifamily) or square feet (for commercial)
- asking_price: float, in dollars
- year_built: integer
- occupancy_pct: float, current physical occupancy as a percentage (e.g. 92.5)
- noi_t12: float, trailing 12-month Net Operating Income in dollars
- noi_proforma: float, projected/stabilized NOI in dollars
- asking_cap_rate: float, cap rate as a percentage (e.g. 5.25)
- gross_potential_rent: float, total gross potential rental income in dollars

DOCUMENT TEXT:
{document_text}"""


def extract_financials(parser_output: dict, api_key: str | None = None) -> dict:
    """
    Extract structured financial data from parsed PDF text using Claude Haiku.

    Args:
        parser_output: Output dict from parser.parse_pdf()
        api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var)

    Returns:
        Dict with extracted fields in the schema:
        { field_name: { value, confidence, source_page, flag } }
        Plus a top-level "extraction_error" key if the API call failed.
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return {"extraction_error": "ANTHROPIC_API_KEY not set."}

    if parser_output.get("error"):
        return {"extraction_error": f"Parser error: {parser_output['error']}"}

    full_text = parser_output.get("full_text", "")
    if not full_text.strip():
        return {"extraction_error": "No text content to extract from."}

    max_chars = 80_000
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars] + "\n\n[...document truncated for token limits...]"

    try:
        import anthropic
    except ImportError:
        return {"extraction_error": "anthropic package not installed. Run: pip install anthropic"}

    client = anthropic.Anthropic(api_key=key)

    user_message = EXTRACTION_PROMPT.format(document_text=full_text)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as e:
        return {"extraction_error": f"API call failed: {e}"}

    raw = response.content[0].text.strip()

    raw_clean = raw
    if raw_clean.startswith("```"):
        lines = raw_clean.split("\n")
        raw_clean = "\n".join(lines[1:])
        if raw_clean.endswith("```"):
            raw_clean = raw_clean[:-3]

    try:
        extracted = json.loads(raw_clean)
    except json.JSONDecodeError as e:
        return {
            "extraction_error": f"Claude returned invalid JSON: {e}",
            "raw_response": raw,
        }

    _enforce_schema(extracted)
    return extracted


EXPECTED_FIELDS = [
    "property_name",
    "location",
    "asset_class",
    "units",
    "asking_price",
    "year_built",
    "occupancy_pct",
    "noi_t12",
    "noi_proforma",
    "asking_cap_rate",
    "gross_potential_rent",
]


def _enforce_schema(data: dict) -> None:
    """Ensure all expected fields exist with correct schema; mutate in place."""
    for field in EXPECTED_FIELDS:
        if field not in data:
            data[field] = {"value": None, "confidence": 0, "source_page": None, "flag": "missing"}
        else:
            entry = data[field]
            if not isinstance(entry, dict):
                data[field] = {"value": entry, "confidence": 50, "source_page": None, "flag": None}
                entry = data[field]

            if "value" not in entry:
                entry["value"] = None
            if "confidence" not in entry:
                entry["confidence"] = 0
            if "source_page" not in entry:
                entry["source_page"] = None
            if "flag" not in entry:
                entry["flag"] = "missing" if entry["value"] is None else None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extractor.py <path_to_pdf>")
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from dotenv import load_dotenv
    load_dotenv()

    from agents.parser import parse_pdf
    parsed = parse_pdf(sys.argv[1])

    if parsed["error"]:
        print(f"Parse error: {parsed['error']}")
        sys.exit(1)

    print(f"Parsed {parsed['page_count']} pages. Extracting financials...")
    result = extract_financials(parsed)

    if "extraction_error" in result:
        print(f"Extraction error: {result['extraction_error']}")
        sys.exit(1)

    print(json.dumps(result, indent=2))
