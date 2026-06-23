"""Display formatting helpers — no UI dependencies."""

import re

DOLLAR_FIELDS = {"asking_price", "noi_t12", "noi_proforma", "gross_potential_rent"}
PCT_FIELDS    = {"occupancy_pct", "asking_cap_rate"}


def fmt_value(field: str, value) -> str:
    if value is None:
        return "—"
    if field in DOLLAR_FIELDS:
        return f"${value:,.0f}"
    if field in PCT_FIELDS:
        return f"{value:.2f}%"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def fmt_compare(key: str, value) -> str:
    if value is None:
        return "—"
    dollar_keys = {"asking_price", "noi_t12"}
    pct_keys    = {"occupancy_pct", "asking_cap_rate", "cap_rate_inplace",
                   "cap_rate_proforma", "debt_yield", "cash_on_cash"}
    if key in dollar_keys:
        return f"${value:,.0f}"
    if key in pct_keys:
        return f"{value:.2f}%"
    if key == "dscr":
        return f"{value:.2f}x"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def confidence_dot(conf: int) -> str:
    if conf >= 80:
        return "🟢"
    if conf >= 50:
        return "🟡"
    return "🔴"


def extract_go_no_go(memo_markdown: str) -> str:
    m = re.search(r"\*\*(NO-GO|CONDITIONAL GO|GO)\*\*", memo_markdown or "")
    if not m:
        return "Unknown"
    return {"NO-GO": "No-Go", "CONDITIONAL GO": "Conditional Go", "GO": "Go"}.get(
        m.group(1), m.group(1)
    )


def compute_sensitivity_row(
    asking_price: float,
    noi: float,
    ltv: float,
    rate: float,
    am_years: int,
):
    """Return (dscr, cap_rate_pct) for one sensitivity scenario. Returns (None, None) on invalid inputs."""
    if not asking_price or not noi or not ltv or not rate or not am_years:
        return None, None
    loan = asking_price * ltv
    r = rate / 12
    n = am_years * 12
    if r == 0 or n == 0:
        return None, None
    monthly = loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    annual_debt = monthly * 12
    dscr = noi / annual_debt if annual_debt else None
    cap_rate = noi / asking_price * 100
    return dscr, cap_rate
