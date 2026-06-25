"""Shared financial math utilities — no UI or service dependencies."""

from __future__ import annotations


def compute_simple_irr_and_multiple(
    purchase_price: float,
    year1_noi: float,
    noi_growth_rate: float = 0.025,
    exit_cap_rate: float = 0.055,
    hold_years: int = 5,
) -> tuple:
    """
    Unlevered IRR and equity multiple using a constant-growth NOI model.

    Cash flows:
      CF_0        = -purchase_price
      CF_1…n-1   = NOI_1 × (1+g)^(t-1)
      CF_n (exit) = NOI_n + NOI_n / exit_cap_rate

    Returns (irr, equity_multiple) where:
      - irr            is the decimal annualised rate (e.g. 0.12 = 12 %) or None
      - equity_multiple is total inflows / purchase_price (always computed when inputs valid)

    Returns (None, None) when any required input is missing or invalid.
    """
    if not purchase_price or not year1_noi or not exit_cap_rate:
        return None, None
    if purchase_price <= 0 or year1_noi <= 0 or exit_cap_rate <= 0:
        return None, None

    cfs: list[float] = [-purchase_price]
    for t in range(1, hold_years + 1):
        noi_t = year1_noi * (1 + noi_growth_rate) ** (t - 1)
        terminal = (noi_t / exit_cap_rate) if t == hold_years else 0.0
        cfs.append(noi_t + terminal)

    equity_multiple = round(sum(cfs[1:]) / purchase_price, 4)

    def _npv(r: float) -> float:
        return sum(c / (1 + r) ** i for i, c in enumerate(cfs))

    irr: float | None = None
    try:
        lo, hi = -0.90, 10.0
        if _npv(lo) * _npv(hi) <= 0:
            for _ in range(200):
                mid = (lo + hi) / 2
                if _npv(mid) > 0:
                    lo = mid
                else:
                    hi = mid
            irr = round((lo + hi) / 2, 6)
    except Exception:
        irr = None

    return irr, equity_multiple
