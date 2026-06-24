"""Pre-computed sample deal dicts for demonstration. No PDFs or API calls needed."""

SAMPLE_NAMES = [
    "Example 1 – Core GO Deal",
    "Example 2 – Value-Add NO-GO",
    "Example 3 – Missing Data NEED INFO",
]

# ---------------------------------------------------------------------------
# Example 1 — 200-unit core multifamily, Austin TX → GO
# Extracted data: price $14M, T-12 NOI $1.05M → cap 7.5%, DSCR 1.41x at defaults
# ---------------------------------------------------------------------------
_DEAL_1 = {
    "parsed": {
        "full_text": (
            "Riverside Commons — 200-unit Class B multifamily, Austin TX. "
            "Built 2001. Asking price $14,000,000. T-12 NOI $1,050,000. "
            "Proforma NOI $1,120,000. Occupancy 94%. "
            "Gross potential rent $1,680,000. Asking cap rate 7.50%."
        ),
        "error": None,
    },
    "extracted": {
        "property_name":        {"value": "Riverside Commons",  "confidence": 97, "source_page": 1,  "flag": None},
        "location":             {"value": "Austin, TX",         "confidence": 95, "source_page": 1,  "flag": None},
        "asset_class":          {"value": "Multifamily",        "confidence": 98, "source_page": 1,  "flag": None},
        "units":                {"value": 200,                   "confidence": 96, "source_page": 2,  "flag": None},
        "asking_price":         {"value": 14_000_000,           "confidence": 99, "source_page": 4,  "flag": None},
        "year_built":           {"value": 2001,                 "confidence": 93, "source_page": 2,  "flag": None},
        "occupancy_pct":        {"value": 94.0,                 "confidence": 91, "source_page": 7,  "flag": None},
        "noi_t12":              {"value": 1_050_000,            "confidence": 94, "source_page": 10, "flag": None},
        "noi_proforma":         {"value": 1_120_000,            "confidence": 82, "source_page": 12, "flag": None},
        "asking_cap_rate":      {"value": 7.50,                 "confidence": 96, "source_page": 4,  "flag": None},
        "gross_potential_rent": {"value": 1_680_000,            "confidence": 88, "source_page": 8,  "flag": None},
    },
    "underwriter": {
        "loan_assumptions": {
            "ltv": 0.70, "rate": 0.065, "amortization_years": 30, "hold_period_years": 5,
            "loan_amount": 9_800_000, "equity_invested": 4_200_000, "annual_debt_service": 743_349,
        },
        "metrics": {
            "cap_rate_inplace":  {"value": 7.50, "formatted": "7.50%", "formula_used": "NOI (T-12) / Asking Price × 100",       "benchmark": "> 5.0%",  "status": "pass"},
            "cap_rate_proforma": {"value": 8.00, "formatted": "8.00%", "formula_used": "NOI (Proforma) / Asking Price × 100",    "benchmark": "> 5.0%",  "status": "pass"},
            "dscr":              {"value": 1.41, "formatted": "1.41x", "formula_used": "NOI (T-12) / Annual Debt Service",       "benchmark": "> 1.25x", "status": "pass"},
            "debt_yield":        {"value": 10.71, "formatted": "10.71%", "formula_used": "NOI (T-12) / Loan Amount × 100",      "benchmark": "> 8.0%",  "status": "pass"},
            "cash_on_cash":      {"value": 7.30, "formatted": "7.30%",  "formula_used": "(NOI T-12 − Debt Service) / Equity",   "benchmark": "> 7.0%",  "status": "pass"},
        },
        "deal_score": {"score": 92.3, "label": "Strong", "explanation": "Cap rate 7.50% → 40pts; DSCR 1.41x → 52pts"},
        "equity_multiple": {"value": 1.0, "status": "needs_input", "note": "Placeholder — re-run with exit assumptions after 5-yr hold."},
        "underwriter_error": None,
    },
    "risk": {
        "flags": [
            {
                "flag_name": "NOI Inflation",
                "severity": "critical",
                "triggered": False,
                "detail": "Proforma NOI ($1,120,000) is 6.7% above T-12 NOI ($1,050,000) — growth assumption is within the acceptable 10% range and appears well-supported by market rent trends.",
            },
            {
                "flag_name": "DSCR Below Threshold",
                "severity": "critical",
                "triggered": False,
                "detail": "DSCR of 1.41x exceeds the 1.25x lender minimum at standard 70% LTV. Debt coverage is comfortable with a 13% cushion above threshold.",
            },
            {
                "flag_name": "Occupancy Risk",
                "severity": "warning",
                "triggered": False,
                "detail": "Current occupancy of 94% is above the 90% lender threshold. Vacancy risk is low; the asset appears stabilized.",
            },
            {
                "flag_name": "Cap Rate Compression",
                "severity": "warning",
                "triggered": False,
                "detail": "In-place cap rate of 7.50% is well above the 5.0% pass threshold. Cap rate compression risk is minimal in this pricing range.",
            },
            {
                "flag_name": "Year Built / CapEx Risk",
                "severity": "warning",
                "triggered": False,
                "detail": "Asset was built in 2001 (24 years old). Moderate CapEx exposure — budget $250–$350/unit/year for reserves. Roof and HVAC systems may need replacement within the hold period.",
            },
        ],
        "critical_count": 0,
        "triggered_count": 0,
    },
    "market": {
        "cap_rate_benchmark": "5.00–5.75%",
        "rent_growth_trend": {
            "direction": "positive",
            "reason": "Austin continues to benefit from strong tech sector employment and high in-migration, supporting 3–5% annual rent growth in Class B product.",
        },
        "deal_positioning": "above market",
        "submarket_summary": (
            "Austin, TX remains one of the strongest multifamily markets in the Sun Belt. "
            "High in-migration, technology sector employment, and constrained Class B supply "
            "position this asset favorably. The deal is priced above the market cap rate "
            "benchmark, indicating strong in-place yield relative to submarket peers."
        ),
        "footer": "Market data synthesized from AI research. Verify against CoStar or Crexi before IC submission.",
    },
    "report": {
        "property_name": "Riverside Commons",
        "memo_markdown": """# IC Memo — Riverside Commons

**Date:** June 2026 | **Analyst:** DealScreen AI | **Classification:** Sample Deal

---

## Executive Summary

**Recommendation: Go**

Riverside Commons is a 200-unit Class B multifamily asset in Austin, TX (2001 vintage) offered at $14.0M ($70,000/unit). The deal demonstrates strong fundamentals across all key metrics: T-12 cap rate of 7.50%, DSCR of 1.41x, debt yield of 10.71%, and cash-on-cash of 7.30%—all clearing lender thresholds with meaningful cushion. Zero risk flags triggered. Austin submarket supports a positive rent growth thesis.

---

## Property Overview

| Field | Value |
|---|---|
| Address | Austin, TX |
| Units | 200 |
| Year Built | 2001 |
| Asking Price | $14,000,000 |
| Price / Unit | $70,000 |
| Occupancy | 94% |
| T-12 NOI | $1,050,000 |

---

## Underwriting Summary (70% LTV · 6.5% · 30-yr)

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Cap Rate (T-12) | 7.50% | > 5.0% | ✅ Pass |
| Cap Rate (Proforma) | 8.00% | > 5.0% | ✅ Pass |
| DSCR | 1.41x | > 1.25x | ✅ Pass |
| Debt Yield | 10.71% | > 8.0% | ✅ Pass |
| Cash-on-Cash | 7.30% | > 7.0% | ✅ Pass |

---

## Risk Assessment

All 5 risk flags clear. No critical or warning conditions triggered.

---

## IC Recommendation

**Go** — Strong in-place metrics across all underwriting thresholds. Austin submarket provides conviction for rent growth thesis. Recommend proceeding to full due diligence and lender engagement at current terms.
""",
    },
}

# ---------------------------------------------------------------------------
# Example 2 — 48-unit value-add, Memphis TN → NO-GO
# Price $3.2M, T-12 NOI $104K → cap 3.25%, DSCR 0.61x; proforma NOI +174% triggers flag
# ---------------------------------------------------------------------------
_DEAL_2 = {
    "parsed": {
        "full_text": (
            "Elmwood Gardens — 48-unit Class C multifamily, Memphis TN. "
            "Built 1972. Asking price $3,200,000. T-12 NOI $104,000. "
            "Proforma NOI $285,000 (post-renovation stabilization). "
            "Current occupancy 71%. Gross potential rent $432,000. Asking cap rate 3.25%."
        ),
        "error": None,
    },
    "extracted": {
        "property_name":        {"value": "Elmwood Gardens", "confidence": 96, "source_page": 1,  "flag": None},
        "location":             {"value": "Memphis, TN",     "confidence": 94, "source_page": 1,  "flag": None},
        "asset_class":          {"value": "Multifamily",     "confidence": 98, "source_page": 1,  "flag": None},
        "units":                {"value": 48,                 "confidence": 95, "source_page": 2,  "flag": None},
        "asking_price":         {"value": 3_200_000,         "confidence": 99, "source_page": 3,  "flag": None},
        "year_built":           {"value": 1972,              "confidence": 92, "source_page": 2,  "flag": None},
        "occupancy_pct":        {"value": 71.0,              "confidence": 89, "source_page": 6,  "flag": None},
        "noi_t12":              {"value": 104_000,           "confidence": 85, "source_page": 9,  "flag": None},
        "noi_proforma":         {"value": 285_000,           "confidence": 60, "source_page": 11, "flag": None},
        "asking_cap_rate":      {"value": 3.25,              "confidence": 90, "source_page": 3,  "flag": None},
        "gross_potential_rent": {"value": 432_000,           "confidence": 75, "source_page": 7,  "flag": None},
    },
    "underwriter": {
        "loan_assumptions": {
            "ltv": 0.70, "rate": 0.065, "amortization_years": 30, "hold_period_years": 5,
            "loan_amount": 2_240_000, "equity_invested": 960_000, "annual_debt_service": 169_884,
        },
        "metrics": {
            "cap_rate_inplace":  {"value": 3.25, "formatted": "3.25%",  "formula_used": "NOI (T-12) / Asking Price × 100",     "benchmark": "> 5.0%",  "status": "fail"},
            "cap_rate_proforma": {"value": 8.91, "formatted": "8.91%",  "formula_used": "NOI (Proforma) / Asking Price × 100", "benchmark": "> 5.0%",  "status": "pass"},
            "dscr":              {"value": 0.61, "formatted": "0.61x",  "formula_used": "NOI (T-12) / Annual Debt Service",    "benchmark": "> 1.25x", "status": "fail"},
            "debt_yield":        {"value": 4.64, "formatted": "4.64%",  "formula_used": "NOI (T-12) / Loan Amount × 100",     "benchmark": "> 8.0%",  "status": "fail"},
            "cash_on_cash":      {"value": -6.86, "formatted": "-6.86%", "formula_used": "(NOI T-12 − Debt Service) / Equity", "benchmark": "> 7.0%",  "status": "fail"},
        },
        "deal_score": {"score": 3.0, "label": "Weak", "explanation": "Cap rate 3.25% → 0pts (below 3.0% floor); DSCR 0.61x → 0pts (below 0.80x floor)"},
        "equity_multiple": {"value": 1.0, "status": "needs_input", "note": "Placeholder — re-run with exit assumptions after 5-yr hold."},
        "underwriter_error": None,
    },
    "risk": {
        "flags": [
            {
                "flag_name": "NOI Inflation",
                "severity": "critical",
                "triggered": True,
                "detail": (
                    "Proforma NOI ($285,000) is 174% above T-12 NOI ($104,000) — an extraordinary "
                    "jump with no documented lease-up plan or signed LOIs. The seller is pricing on "
                    "speculative stabilization from a distressed 71% occupancy base. Request a "
                    "detailed rent roll and renovation budget before advancing."
                ),
            },
            {
                "flag_name": "DSCR Below Threshold",
                "severity": "critical",
                "triggered": True,
                "detail": (
                    "DSCR of 0.61x is critically below the 1.25x lender minimum. No conventional "
                    "lender will underwrite this deal at current T-12 NOI and 70% LTV. The entire "
                    "business plan depends on executing the value-add renovation and achieving full "
                    "lease-up — a multi-year execution risk."
                ),
            },
            {
                "flag_name": "Occupancy Risk",
                "severity": "warning",
                "triggered": True,
                "detail": (
                    "Current occupancy of 71% is well below the 90% lender threshold. In Memphis "
                    "Class C product, high vacancy may reflect deferred maintenance, management "
                    "issues, or localized market softness — all of which increase stabilization risk."
                ),
            },
            {
                "flag_name": "Cap Rate Compression",
                "severity": "warning",
                "triggered": True,
                "detail": (
                    "In-place cap rate of 3.25% is below the 4.0% warning floor. Seller is pricing "
                    "entirely on proforma, creating significant buyer-pays-for-upside risk if the "
                    "renovation does not deliver projected NOI."
                ),
            },
            {
                "flag_name": "Year Built / CapEx Risk",
                "severity": "warning",
                "triggered": True,
                "detail": (
                    "Asset was built in 1972 (54 years old). Expect significant capital needs: "
                    "roof, HVAC, plumbing, and electrical systems are likely at or past end of life. "
                    "Budget $5,000–$10,000/unit ($240,000–$480,000 total) for capital repairs "
                    "before stabilization is achievable."
                ),
            },
        ],
        "critical_count": 2,
        "triggered_count": 5,
    },
    "market": {
        "cap_rate_benchmark": "6.50–8.00%",
        "rent_growth_trend": {
            "direction": "flat",
            "reason": "Memphis Class C multifamily has seen limited rent growth over the past 24 months due to new supply delivery and weaker employment fundamentals relative to Sun Belt peers.",
        },
        "deal_positioning": "above market",
        "submarket_summary": (
            "Memphis, TN offers lower absolute pricing but faces headwinds including slower job "
            "growth and an oversupplied Class C segment. A 3.25% in-place cap rate is significantly "
            "above the 6.50–8.00% market benchmark, indicating the seller is pricing a "
            "distressed asset at stabilized value — a high-risk proposition for any buyer."
        ),
        "footer": "Market data synthesized from AI research. Verify against CoStar or Crexi before IC submission.",
    },
    "report": {
        "property_name": "Elmwood Gardens",
        "memo_markdown": """# IC Memo — Elmwood Gardens

**Date:** June 2026 | **Analyst:** DealScreen AI | **Classification:** Sample Deal

---

## Executive Summary

**Recommendation: No-Go**

Elmwood Gardens is a 48-unit Class C multifamily asset in Memphis, TN (1972 vintage) offered at $3.2M ($66,667/unit). While the proforma cap rate appears attractive at 8.91%, in-place fundamentals are severely distressed: T-12 DSCR of 0.61x, 71% occupancy, and all 5 risk flags triggered including 2 critical. The proforma assumes a 174% NOI increase from an unverified value-add plan. The risk-adjusted return does not compensate for execution risk in a flat Memphis Class C submarket.

---

## Property Overview

| Field | Value |
|---|---|
| Address | Memphis, TN |
| Units | 48 |
| Year Built | 1972 |
| Asking Price | $3,200,000 |
| Price / Unit | $66,667 |
| Occupancy | 71% |
| T-12 NOI | $104,000 |

---

## Underwriting Summary (70% LTV · 6.5% · 30-yr)

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Cap Rate (T-12) | 3.25% | > 5.0% | 🔴 Fail |
| Cap Rate (Proforma) | 8.91% | > 5.0% | ✅ Pass (speculative) |
| DSCR | 0.61x | > 1.25x | 🔴 Critical |
| Debt Yield | 4.64% | > 8.0% | 🔴 Fail |
| Cash-on-Cash | -6.86% | > 7.0% | 🔴 Fail |

---

## Risk Assessment

🚨 **2 Critical Flags**: NOI Inflation (+174%) and DSCR Below Threshold (0.61x)
⚠️ **3 Warning Flags**: Occupancy Risk (71%), Cap Rate Compression, CapEx Risk (1972 vintage)

---

## IC Recommendation

**No-Go** — Five of five risk flags triggered, including two critical. Seller is pricing a distressed asset at speculative stabilized value. Pass unless: (1) price is reduced to support 1.0x+ in-place DSCR, (2) deal is structured all-cash with a defined bridge exit, and (3) a signed renovation plan with contractor bids is provided.
""",
    },
}

# ---------------------------------------------------------------------------
# Example 3 — Missing data, Denver CO → NEED INFO
# Most financial fields absent from the OM excerpt
# ---------------------------------------------------------------------------
_DEAL_3 = {
    "parsed": {
        "full_text": (
            "Summit Ridge Apartments — offering memorandum excerpt. "
            "Property located in Denver, CO. Multifamily asset. "
            "Asking price $12,000,000. "
            "Note: Full financial statements and rent roll not included in this excerpt."
        ),
        "error": None,
    },
    "extracted": {
        "property_name":        {"value": "Summit Ridge Apartments", "confidence": 95, "source_page": 1,    "flag": None},
        "location":             {"value": "Denver, CO",              "confidence": 93, "source_page": 1,    "flag": None},
        "asset_class":          {"value": "Multifamily",             "confidence": 97, "source_page": 1,    "flag": None},
        "units":                {"value": None,   "confidence": 0, "source_page": None, "flag": "missing"},
        "asking_price":         {"value": 12_000_000, "confidence": 96, "source_page": 3, "flag": None},
        "year_built":           {"value": None,   "confidence": 0, "source_page": None, "flag": "missing"},
        "occupancy_pct":        {"value": None,   "confidence": 0, "source_page": None, "flag": "missing"},
        "noi_t12":              {"value": None,   "confidence": 0, "source_page": None, "flag": "missing"},
        "noi_proforma":         {"value": None,   "confidence": 0, "source_page": None, "flag": "missing"},
        "asking_cap_rate":      {"value": None,   "confidence": 0, "source_page": None, "flag": "missing"},
        "gross_potential_rent": {"value": None,   "confidence": 0, "source_page": None, "flag": "missing"},
    },
    "underwriter": {
        "loan_assumptions": {
            "ltv": 0.70, "rate": 0.065, "amortization_years": 30, "hold_period_years": 5,
            "loan_amount": 8_400_000, "equity_invested": 3_600_000, "annual_debt_service": 637_013,
        },
        "metrics": {
            "cap_rate_inplace":  {"value": None, "formatted": "—", "formula_used": "NOI (T-12) / Asking Price × 100",       "benchmark": "> 5.0%",  "status": "missing"},
            "cap_rate_proforma": {"value": None, "formatted": "—", "formula_used": "NOI (Proforma) / Asking Price × 100",   "benchmark": "> 5.0%",  "status": "missing"},
            "dscr":              {"value": None, "formatted": "—", "formula_used": "NOI (T-12) / Annual Debt Service",      "benchmark": "> 1.25x", "status": "missing"},
            "debt_yield":        {"value": None, "formatted": "—", "formula_used": "NOI (T-12) / Loan Amount × 100",       "benchmark": "> 8.0%",  "status": "missing"},
            "cash_on_cash":      {"value": None, "formatted": "—", "formula_used": "(NOI T-12 − Debt Service) / Equity",   "benchmark": "> 7.0%",  "status": "missing"},
        },
        "deal_score": {"score": 0.0, "label": "Weak", "explanation": "Insufficient data — T-12 NOI and occupancy are missing; cannot score."},
        "equity_multiple": {"value": None, "status": "missing", "note": "Cannot compute without NOI."},
        "underwriter_error": None,
    },
    "risk": {
        "flags": [
            {
                "flag_name": "NOI Inflation",
                "severity": "critical",
                "triggered": False,
                "detail": "T-12 and proforma NOI are both missing — NOI inflation cannot be evaluated. Request the full T-12 operating statement.",
            },
            {
                "flag_name": "DSCR Below Threshold",
                "severity": "critical",
                "triggered": True,
                "detail": (
                    "DSCR cannot be calculated because T-12 NOI is not available in the OM excerpt. "
                    "Without debt service coverage data, no lender can underwrite this deal. "
                    "Request the complete trailing 12-month P&L from the broker before advancing."
                ),
            },
            {
                "flag_name": "Occupancy Risk",
                "severity": "warning",
                "triggered": True,
                "detail": (
                    "Occupancy data is absent from the document. Inability to assess current "
                    "occupancy prevents evaluation of stabilization risk or lender eligibility. "
                    "Request a current rent roll with lease expiration dates."
                ),
            },
            {
                "flag_name": "Cap Rate Compression",
                "severity": "warning",
                "triggered": False,
                "detail": "In-place cap rate cannot be calculated without T-12 NOI. Request operating statements.",
            },
            {
                "flag_name": "Year Built / CapEx Risk",
                "severity": "warning",
                "triggered": True,
                "detail": (
                    "Year built is not available in the document. CapEx reserve requirements are "
                    "unknown. Request the property condition assessment (PCA) and inspection report."
                ),
            },
        ],
        "critical_count": 1,
        "triggered_count": 3,
    },
    "market": {
        "cap_rate_benchmark": "4.75–5.50%",
        "rent_growth_trend": {
            "direction": "positive",
            "reason": "Denver multifamily benefits from tech and aerospace employment, though new supply is moderating growth in 2025–2026.",
        },
        "deal_positioning": "at market",
        "submarket_summary": (
            "Denver, CO is a high-conviction multifamily market with strong long-term fundamentals. "
            "However, the absence of in-place financial data prevents a definitive market positioning "
            "assessment. Once T-12 financials are obtained, compare in-place cap rate against the "
            "4.75–5.50% Denver benchmark."
        ),
        "footer": "Market data synthesized from AI research. Verify against CoStar or Crexi before IC submission.",
    },
    "report": {
        "property_name": "Summit Ridge Apartments",
        "memo_markdown": """# IC Memo — Summit Ridge Apartments

**Date:** June 2026 | **Analyst:** DealScreen AI | **Classification:** Sample Deal

---

## Executive Summary

**Recommendation: Conditional Go (Need More Info)**

Summit Ridge Apartments is a multifamily asset in Denver, CO offered at $12.0M. While Denver's submarket fundamentals are favorable, the Offering Memorandum as provided is missing critical data: T-12 NOI, occupancy, unit count, year built, and cap rate. DealScreen AI cannot complete underwriting without these inputs. **Analyst action required: request a complete T-12 operating statement and current rent roll before proceeding.**

---

## Missing Data Checklist

The following fields were not found in the document excerpt:

| Field | Status | Required For |
|---|---|---|
| T-12 NOI | ❌ Missing | DSCR, Cap Rate, Debt Yield, Cash-on-Cash |
| Occupancy % | ❌ Missing | Stabilization risk, lender eligibility |
| Unit Count | ❌ Missing | Per-unit pricing benchmarks |
| Year Built | ❌ Missing | CapEx reserve estimation |
| Proforma NOI | ❌ Missing | Forward-looking metrics |
| Gross Potential Rent | ❌ Missing | Revenue upside assessment |

---

## What Is Known

- **Location**: Denver, CO (strong multifamily market)
- **Asset Class**: Multifamily
- **Asking Price**: $12,000,000
- **Market Cap Rate Benchmark**: 4.75–5.50%

---

## IC Recommendation

**Conditional Go (Need More Info)** — Strong market thesis for Denver, but an incomplete OM prevents any underwriting. Next steps: (1) request full T-12 operating statement from broker, (2) obtain current rent roll with occupancy and lease expirations, (3) request property condition assessment for CapEx planning.
""",
    },
}

SAMPLE_DEALS = [_DEAL_1, _DEAL_2, _DEAL_3]
