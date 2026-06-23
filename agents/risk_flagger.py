"""Agent 4: Risk Flagger — deterministic triggers + Claude Haiku contextual detail."""

import json
import os
import sys

SYSTEM_PROMPT = """You are a senior commercial real estate risk analyst. You will be given a list of triggered risk flags for a CRE deal, along with the key financial data that caused each flag to trigger.

For each flag, write a concise 1-2 sentence `detail` explaining:
- Why this specific metric or data gap is a concern in the current CRE lending environment
- What a buyer or lender should verify or watch out for

Be specific to the numbers provided. Do not be generic. Do not add new flags.
Return ONLY a valid JSON array with the same flags in the same order, each having an updated "detail" field."""


def _get(d: dict, field: str):
    entry = d.get(field)
    if isinstance(entry, dict):
        return entry.get("value")
    return None


def _pct(val) -> str:
    return f"{val:.1f}%" if val is not None else "N/A"


def _x(val) -> str:
    return f"{val:.2f}x" if val is not None else "N/A"


def _compute_triggers(extracted: dict, underwriter: dict) -> list[dict]:
    """Evaluate all 5 flag conditions deterministically."""
    flags = []
    metrics = underwriter.get("metrics", {})

    noi_t12 = _get(extracted, "noi_t12")
    noi_proforma = _get(extracted, "noi_proforma")
    occupancy = _get(extracted, "occupancy_pct")
    asking_cap = _get(extracted, "asking_cap_rate")
    dscr_val = metrics.get("dscr", {}).get("value")

    # Flag 1: NOI inflation
    noi_inflation_triggered = False
    noi_inflation_detail = ""
    if noi_t12 and noi_proforma and noi_t12 > 0:
        pct_above = (noi_proforma - noi_t12) / noi_t12 * 100
        if pct_above > 10:
            noi_inflation_triggered = True
            noi_inflation_detail = (
                f"Proforma NOI (${noi_proforma:,.0f}) is {pct_above:.1f}% above "
                f"T-12 NOI (${noi_t12:,.0f}) with no documented explanation. "
                "Verify revenue growth assumptions against rent rolls and market rents."
            )
    flags.append({
        "flag_name": "NOI Inflation",
        "severity": "critical",
        "triggered": noi_inflation_triggered,
        "detail": noi_inflation_detail or (
            f"Proforma NOI is within 10% of T-12 NOI — growth assumption appears reasonable."
        ),
    })

    # Flag 2: Occupancy risk
    occ_triggered = occupancy is not None and occupancy < 90.0
    flags.append({
        "flag_name": "Occupancy Risk",
        "severity": "warning",
        "triggered": occ_triggered,
        "detail": (
            f"Physical occupancy is {_pct(occupancy)}, below the 90% lender threshold. "
            "Many agency lenders require ≥90% occupancy for 90 days before closing."
        ) if occ_triggered else (
            f"Occupancy at {_pct(occupancy)} meets the standard lender threshold of 90%."
        ),
    })

    # Flag 3: Thin debt coverage
    dscr_triggered = dscr_val is not None and dscr_val < 1.20
    flags.append({
        "flag_name": "Thin Debt Coverage",
        "severity": "critical",
        "triggered": dscr_triggered,
        "detail": (
            f"DSCR of {_x(dscr_val)} is below the 1.20x minimum required by most lenders. "
            "This leaves limited margin for NOI softness and may prevent financing at the assumed LTV."
        ) if dscr_triggered else (
            f"DSCR of {_x(dscr_val)} provides adequate coverage above the 1.20x minimum threshold."
        ),
    })

    # Flag 4: Missing critical data
    critical_fields = [
        "asking_price", "noi_t12", "occupancy_pct", "units", "year_built",
    ]
    missing = [
        f for f in critical_fields
        if isinstance(extracted.get(f), dict) and extracted[f].get("flag") == "missing"
    ]
    missing_triggered = len(missing) > 0
    flags.append({
        "flag_name": "Missing Critical Data",
        "severity": "critical" if missing_triggered else "info",
        "triggered": missing_triggered,
        "detail": (
            f"The following critical fields were not found in the document: "
            f"{', '.join(missing)}. These are required for accurate underwriting."
        ) if missing_triggered else (
            "All critical underwriting data fields were found in the document."
        ),
    })

    # Flag 5: Cap rate compression
    cap_triggered = asking_cap is not None and asking_cap < 5.0
    flags.append({
        "flag_name": "Cap Rate Compression",
        "severity": "warning",
        "triggered": cap_triggered,
        "detail": (
            f"Asking cap rate of {_pct(asking_cap)} is below 5.0% in a 6.5%+ rate environment, "
            "creating negative leverage. Debt cost exceeds the property's yield — equity returns "
            "depend entirely on NOI growth or appreciation."
        ) if cap_triggered else (
            f"Asking cap rate of {_pct(asking_cap)} provides positive leverage above the assumed 6.5% debt cost."
        ),
    })

    # Flag 6: OM vs T-12 discrepancy
    om_triggered = False
    om_detail = ""
    if noi_t12 and noi_proforma and noi_t12 > 0:
        gap_pct = (noi_proforma - noi_t12) / noi_t12 * 100
        if noi_proforma > noi_t12 * 1.10:
            om_triggered = True
            om_detail = (
                f"OM projects ${noi_proforma:,.0f} proforma NOI vs ${noi_t12:,.0f} T-12 actual "
                f"— {gap_pct:.1f}% gap with no stated justification. "
                "Request seller's revenue and expense reconciliation before underwriting the proforma."
            )
    flags.append({
        "flag_name": "OM vs T-12 Discrepancy",
        "severity": "critical",
        "triggered": om_triggered,
        "detail": om_detail or (
            "Proforma NOI is within 10% of T-12 actual — OM projections appear grounded in trailing performance."
        ),
    })

    # Flag 7: Occupancy data quality (low confidence = possible OM vs rent roll mismatch)
    occ_entry = extracted.get("occupancy_pct") if hasattr(extracted, "get") else None
    occ_conf = occ_entry.get("confidence", 100) if isinstance(occ_entry, dict) else 100
    occ_quality_triggered = occ_conf < 70
    flags.append({
        "flag_name": "Occupancy Data Quality",
        "severity": "info",
        "triggered": occ_quality_triggered,
        "detail": (
            f"Occupancy confidence is {occ_conf}% — extractor could not clearly locate a single, "
            "authoritative figure. Reported occupancy may reflect OM marketing copy rather than the "
            "certified rent roll; request the most recent signed rent roll to verify."
        ) if occ_quality_triggered else (
            f"Occupancy figure extracted with {occ_conf}% confidence — source appears reliable."
        ),
    })

    return flags


def _enrich_with_haiku(flags: list[dict], extracted: dict, underwriter: dict, api_key: str) -> list[dict]:
    """Call Claude Haiku to rewrite detail strings with deal-specific CRE context."""
    triggered = [f for f in flags if f["triggered"]]
    if not triggered:
        return flags

    try:
        import anthropic
    except ImportError:
        return flags

    loan = underwriter.get("loan_assumptions", {})
    context = {
        "asking_price": _get(extracted, "asking_price"),
        "noi_t12": _get(extracted, "noi_t12"),
        "noi_proforma": _get(extracted, "noi_proforma"),
        "occupancy_pct": _get(extracted, "occupancy_pct"),
        "asking_cap_rate": _get(extracted, "asking_cap_rate"),
        "asset_class": _get(extracted, "asset_class"),
        "loan_amount": loan.get("loan_amount"),
        "annual_debt_service": loan.get("annual_debt_service"),
        "dscr": underwriter.get("metrics", {}).get("dscr", {}).get("value"),
    }

    user_msg = (
        f"Deal context: {json.dumps(context)}\n\n"
        f"Triggered flags to enrich:\n{json.dumps(triggered, indent=2)}"
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:]).rstrip("`").strip()
        enriched = json.loads(raw)
        if isinstance(enriched, list) and len(enriched) == len(triggered):
            for original, updated in zip(triggered, enriched):
                original["detail"] = updated.get("detail", original["detail"])
    except Exception:
        pass

    return flags


def flag_risks(extracted: dict, underwriter: dict, api_key=None) -> dict:
    """
    Evaluate risk flags deterministically, then enrich triggered flags via Haiku.

    Returns:
        {
            "flags": [ { flag_name, severity, triggered, detail }, ... ],
            "triggered_count": int,
            "critical_count": int,
            "flagger_error": None | str,
        }
    """
    if underwriter.get("underwriter_error"):
        return {
            "flags": [],
            "triggered_count": 0,
            "critical_count": 0,
            "flagger_error": f"Underwriter error: {underwriter['underwriter_error']}",
        }

    flags = _compute_triggers(extracted, underwriter)

    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if key:
        flags = _enrich_with_haiku(flags, extracted, underwriter, key)

    triggered_count = sum(1 for f in flags if f["triggered"])
    critical_count = sum(1 for f in flags if f["triggered"] and f["severity"] == "critical")

    return {
        "flags": flags,
        "triggered_count": triggered_count,
        "critical_count": critical_count,
        "flagger_error": None,
    }


if __name__ == "__main__":
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from dotenv import load_dotenv
    load_dotenv()

    sample_extracted = {
        "asking_price":  {"value": 18_500_000, "confidence": 95, "source_page": 4,  "flag": None},
        "noi_t12":       {"value":    925_000,  "confidence": 88, "source_page": 10, "flag": None},
        "noi_proforma":  {"value":  1_200_000,  "confidence": 75, "source_page": 12, "flag": None},
        "occupancy_pct": {"value":  86.0,        "confidence": 90, "source_page": 7,  "flag": None},
        "asking_cap_rate": {"value": 4.5,        "confidence": 92, "source_page": 4,  "flag": None},
        "asset_class":   {"value": "Multifamily","confidence": 88, "source_page": 1,  "flag": None},
        "units":         {"value": 120,          "confidence": 95, "source_page": 3,  "flag": None},
        "year_built":    {"value": 1998,         "confidence": 85, "source_page": 2,  "flag": None},
    }

    from agents.underwriter import underwrite
    uw = underwrite(sample_extracted)
    result = flag_risks(sample_extracted, uw)
    print(json.dumps(result, indent=2))
