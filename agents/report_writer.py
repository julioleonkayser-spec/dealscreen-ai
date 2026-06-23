"""Agent 6: Report Writer — Claude Opus writes the full Investment Committee Memo."""

import json
import os
import sys
from datetime import date

SYSTEM_PROMPT = """You are a senior real estate investment analyst writing a formal Investment Committee (IC) Memo.

HARD RULES:
1. Never fabricate numbers. Use only values provided in the input JSON.
2. Every number from the extractor must be followed by its source page citation: (p.N).
   If source_page is null, write (source: not cited).
3. Flag every field with flag="missing" explicitly in the relevant section.
4. The Recommendation section MUST reference:
   - The exact DSCR value and whether it passes the 1.25x threshold
   - At least 2 specific triggered risk flags by name
   - The asking cap rate vs the market benchmark range
5. Go / No-Go verdict must be one of: **GO**, **NO-GO**, or **CONDITIONAL GO**.
6. Write in professional investment memo style — concise, factual, no marketing language.
7. Output pure markdown only — no JSON, no code fences."""

MEMO_PROMPT = """Write a complete IC Memo in markdown for this deal using EXACTLY these six sections with these exact headers:

## 1. Executive Summary
## 2. Property Overview
## 3. Financial Analysis
## 4. Risk Assessment
## 5. Market Context
## 6. Recommendation

---

INPUT DATA:

### Extractor Output (extracted financial data with citations)
{extractor_json}

### Underwriter Output (computed metrics)
{underwriter_json}

### Risk Flags
{risk_json}

### Market Research
{market_json}

---

SECTION REQUIREMENTS:

**1. Executive Summary**: 3 sentences only — (1) what the asset is and where, (2) asking price and key metric, (3) go/no-go recommendation preview.

**2. Property Overview**: Markdown table with columns: Field | Value | Source Page. Include: property name, location, asset class, units, asking price, year built, occupancy, gross potential rent. Cite source_page for each row. Mark missing fields as "NOT FOUND IN DOCUMENT".

**3. Financial Analysis**: Markdown table with columns: Metric | Value | Formula | Benchmark | Status. Include all 5 underwriter metrics. Show computed values. Include loan assumptions as a caption below the table.

**4. Risk Assessment**: For triggered flags only — use this format per flag:
> **[SEVERITY] Flag Name**: Detail sentence.

If no flags triggered, write "No risk flags triggered."

**5. Market Context**: Use the market researcher output. Include the submarket summary, cap rate benchmark, rent growth trend with reason, and deal positioning. End with the footer verbatim on its own line.

**6. Recommendation**: State **GO**, **NO-GO**, or **CONDITIONAL GO** on the first line. Then 3-5 bullet points justifying the verdict. MUST cite DSCR, at least 2 triggered flag names, and cap rate vs benchmark. If CONDITIONAL GO, specify the exact conditions."""


def write_report(all_outputs: dict, api_key=None) -> dict:
    """
    Write the full IC Memo in markdown using Claude Opus.

    Args:
        all_outputs: dict with keys:
            "extractor"         — output from extractor.extract_financials()
            "underwriter"       — output from underwriter.underwrite()
            "risk_flagger"      — output from risk_flagger.flag_risks()
            "market_researcher" — output from market_researcher.research_market()
        api_key: Anthropic API key (falls back to env var)

    Returns:
        { "memo_markdown": str, "property_name": str, "writer_error": None | str }
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return _error("ANTHROPIC_API_KEY not set.")

    extractor = all_outputs.get("extractor", {})
    underwriter = all_outputs.get("underwriter", {})
    risk = all_outputs.get("risk_flagger", {})
    market = all_outputs.get("market_researcher", {})

    property_name = _get_value(extractor, "property_name") or "Unknown Property"
    location = _get_value(extractor, "location") or "Unknown Location"

    triggered_flags = [f for f in risk.get("flags", []) if f.get("triggered")]
    risk_summary = {
        "triggered_count": risk.get("triggered_count", 0),
        "critical_count": risk.get("critical_count", 0),
        "triggered_flags": triggered_flags,
    }

    user_msg = MEMO_PROMPT.format(
        extractor_json=json.dumps(extractor, indent=2),
        underwriter_json=json.dumps(underwriter, indent=2),
        risk_json=json.dumps(risk_summary, indent=2),
        market_json=json.dumps(market, indent=2),
    )

    try:
        import anthropic
    except ImportError:
        return _error("anthropic package not installed.")

    header = (
        f"# IC Memo — {property_name}, {location}\n"
        f"**Date:** {date.today().strftime('%B %d, %Y')}  \n"
        f"**Prepared by:** AI Deal Screening Agent (Project Destined Hackathon)\n\n---\n\n"
    )

    try:
        client = anthropic.Anthropic(api_key=key)
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:
        return _error(f"API call failed: {e}")

    memo_body = response.content[0].text.strip()
    full_memo = header + memo_body

    return {
        "memo_markdown": full_memo,
        "property_name": property_name,
        "writer_error": None,
    }


def _get_value(extracted: dict, field: str):
    entry = extracted.get(field)
    if isinstance(entry, dict):
        return entry.get("value")
    return None


def _error(msg: str) -> dict:
    return {
        "memo_markdown": None,
        "property_name": "Unknown",
        "writer_error": msg,
    }


if __name__ == "__main__":
    sys.path.insert(0, __import__("pathlib").Path(__file__).parent.parent.__str__())
    from dotenv import load_dotenv
    load_dotenv()

    sample_extractor = {
        "property_name":    {"value": "The Oakwood", "confidence": 95, "source_page": 1, "flag": None},
        "location":         {"value": "Austin, TX",  "confidence": 90, "source_page": 1, "flag": None},
        "asset_class":      {"value": "Multifamily", "confidence": 88, "source_page": 1, "flag": None},
        "units":            {"value": 120,            "confidence": 95, "source_page": 3, "flag": None},
        "asking_price":     {"value": 18_500_000,     "confidence": 95, "source_page": 4, "flag": None},
        "year_built":       {"value": 1998,           "confidence": 85, "source_page": 2, "flag": None},
        "occupancy_pct":    {"value": 86.0,           "confidence": 90, "source_page": 7, "flag": None},
        "noi_t12":          {"value": 925_000,        "confidence": 88, "source_page": 10, "flag": None},
        "noi_proforma":     {"value": 1_200_000,      "confidence": 75, "source_page": 12, "flag": None},
        "asking_cap_rate":  {"value": 4.5,            "confidence": 92, "source_page": 4, "flag": None},
        "gross_potential_rent": {"value": 1_560_000,  "confidence": 82, "source_page": 8, "flag": None},
    }

    from agents.underwriter import underwrite
    from agents.risk_flagger import flag_risks
    from agents.market_researcher import research_market

    uw = underwrite(sample_extractor)
    risk = flag_risks(sample_extractor, uw)
    market = research_market(sample_extractor)

    result = write_report({
        "extractor": sample_extractor,
        "underwriter": uw,
        "risk_flagger": risk,
        "market_researcher": market,
    })

    if result["writer_error"]:
        print(f"Error: {result['writer_error']}")
    else:
        print(result["memo_markdown"])
