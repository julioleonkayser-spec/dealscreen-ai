"""Agent 3: Underwriter — deterministic CRE financial metric calculations."""

import json
import sys
from pathlib import Path

LTV = 0.70
ANNUAL_RATE = 0.065
AMORTIZATION_YEARS = 30

BENCHMARKS = {
    "cap_rate_inplace":  {"threshold": 5.0,  "label": "> 5.0%",  "warn_floor": 4.0},
    "cap_rate_proforma": {"threshold": 5.0,  "label": "> 5.0%",  "warn_floor": 4.0},
    "dscr":              {"threshold": 1.25, "label": "> 1.25x", "warn_floor": 1.10},
    "debt_yield":        {"threshold": 8.0,  "label": "> 8.0%",  "warn_floor": 6.0},
    "cash_on_cash":      {"threshold": 7.0,  "label": "> 7.0%",  "warn_floor": 4.0},
}


def _get(extracted: dict, field: str):
    """Pull the numeric value from an extracted field dict."""
    entry = extracted.get(field)
    if isinstance(entry, dict):
        return entry.get("value")
    return None


def _monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    """Standard P&I amortizing loan payment formula."""
    r = annual_rate / 12
    n = years * 12
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def _status(value: float, key: str) -> str:
    bench = BENCHMARKS[key]
    if value >= bench["threshold"]:
        return "pass"
    if value >= bench["warn_floor"]:
        return "warn"
    return "fail"


def _metric(value, formula: str, key: str, fmt: str = "pct") -> dict:
    """Build a single metric dict, handling None gracefully."""
    if value is None:
        return {
            "value": None,
            "formatted": "—",
            "formula_used": formula,
            "benchmark": BENCHMARKS[key]["label"],
            "status": "missing",
        }
    formatted = f"{value:.2f}%" if fmt == "pct" else f"{value:.2f}x"
    return {
        "value": round(value, 4),
        "formatted": formatted,
        "formula_used": formula,
        "benchmark": BENCHMARKS[key]["label"],
        "status": _status(value, key),
    }


def compute_deal_score(underwriter_result, market_context=None) -> dict:
    """
    Score a deal 0–100 based on DSCR and in-place cap rate.

    Score = 0.6 × dscr_norm + 0.4 × cap_norm, scaled to 100.
      DSCR:     ≤0.80x → 0,  ≥1.50x → 1
      Cap rate: ≤3.0%  → 0,  ≥7.0%  → 1

    Labels: ≥80 → "Strong", 60–79 → "Borderline", <60 → "Weak"
    """
    metrics  = underwriter_result.get("metrics", {})
    dscr_val = metrics.get("dscr", {}).get("value")
    cap_val  = metrics.get("cap_rate_inplace", {}).get("value")

    dscr_norm = max(0.0, min(1.0, (dscr_val - 0.8) / (1.5 - 0.8))) if dscr_val is not None else 0.0
    cap_norm  = max(0.0, min(1.0, (cap_val  - 3.0) / (7.0 - 3.0))) if cap_val  is not None else 0.0

    score = round((0.6 * dscr_norm + 0.4 * cap_norm) * 100, 1)
    label = "Strong" if score >= 80 else "Borderline" if score >= 60 else "Weak"

    parts = []
    if dscr_val is not None:
        parts.append(f"DSCR {dscr_val:.2f}x → {0.6 * dscr_norm * 100:.0f}pts")
    if cap_val is not None:
        parts.append(f"cap {cap_val:.2f}% → {0.4 * cap_norm * 100:.0f}pts")
    explanation = "; ".join(parts) if parts else "Insufficient data to score"

    return {"score": score, "label": label, "explanation": explanation}


def underwrite(extracted: dict, assumptions: dict = None) -> dict:
    """
    Run deterministic underwriting calculations on extractor output.

    Args:
        extracted:   Output from extractor.extract_financials().
        assumptions: Optional dict with keys ltv (0–1), rate (0–1),
                     amortization_years (int), hold_period_years (int).
                     Falls back to module-level defaults when omitted.

    Returns:
        {
            "loan_assumptions": { ltv, rate, amortization_years, hold_period_years,
                                  loan_amount, equity_invested, annual_debt_service },
            "metrics":    { metric_name: { value, formatted, formula_used, benchmark, status } },
            "equity_multiple": { value, status, note },
            "deal_score": { score, label, explanation },
            "underwriter_error": None | str,
        }
    """
    _a = assumptions or {}
    ltv          = _a.get("ltv",               LTV)
    rate         = _a.get("rate",              ANNUAL_RATE)
    am_years     = _a.get("amortization_years", AMORTIZATION_YEARS)
    hold_period  = _a.get("hold_period_years", 5)

    asking_price = _get(extracted, "asking_price")
    noi_t12      = _get(extracted, "noi_t12")
    noi_proforma = _get(extracted, "noi_proforma")

    if asking_price is None or asking_price <= 0:
        return {
            "loan_assumptions": {},
            "metrics": {},
            "equity_multiple": {"value": None, "status": "missing", "note": "needs_input"},
            "deal_score": {"score": 0.0, "label": "Weak", "explanation": "asking_price missing"},
            "underwriter_error": "asking_price is missing or zero — cannot underwrite.",
        }

    loan_amount         = asking_price * ltv
    equity_invested     = asking_price * (1 - ltv)
    monthly_payment     = _monthly_payment(loan_amount, rate, am_years)
    annual_debt_service = monthly_payment * 12

    loan_assumptions = {
        "ltv":                ltv,
        "rate":               rate,
        "amortization_years": am_years,
        "hold_period_years":  hold_period,
        "loan_amount":        round(loan_amount, 2),
        "equity_invested":    round(equity_invested, 2),
        "annual_debt_service": round(annual_debt_service, 2),
    }

    cap_inplace    = (noi_t12      / asking_price * 100) if noi_t12      else None
    cap_proforma   = (noi_proforma / asking_price * 100) if noi_proforma else None
    dscr_val       = (noi_t12      / annual_debt_service)  if noi_t12      else None
    debt_yield_val = (noi_t12      / loan_amount * 100)    if noi_t12      else None
    first_year_cf  = (noi_t12      - annual_debt_service)  if noi_t12      else None
    coc_val        = (first_year_cf / equity_invested * 100) if first_year_cf is not None else None

    metrics = {
        "cap_rate_inplace":  _metric(cap_inplace,    "NOI (T-12) / Asking Price × 100",               "cap_rate_inplace"),
        "cap_rate_proforma": _metric(cap_proforma,   "NOI (Proforma) / Asking Price × 100",            "cap_rate_proforma"),
        "dscr":              _metric(dscr_val,       "NOI (T-12) / Annual Debt Service",               "dscr",        fmt="mult"),
        "debt_yield":        _metric(debt_yield_val, "NOI (T-12) / Loan Amount × 100",                 "debt_yield"),
        "cash_on_cash":      _metric(coc_val,        "(NOI T-12 − Debt Service) / Equity Invested × 100", "cash_on_cash"),
    }

    equity_multiple = {
        "value":  1.0,
        "status": "needs_input",
        "note":   f"Placeholder 1.0x — re-run with exit assumptions after {hold_period}-yr hold.",
    }

    result = {
        "loan_assumptions": loan_assumptions,
        "metrics":          metrics,
        "equity_multiple":  equity_multiple,
        "underwriter_error": None,
    }
    result["deal_score"] = compute_deal_score(result)
    return result


if __name__ == "__main__":
    sample = {
        "asking_price": {"value": 18_500_000, "confidence": 95, "source_page": 4, "flag": None},
        "noi_t12":      {"value":    925_000, "confidence": 88, "source_page": 10, "flag": None},
        "noi_proforma": {"value":  1_050_000, "confidence": 75, "source_page": 12, "flag": None},
    }
    result = underwrite(sample)
    print(json.dumps(result, indent=2))
