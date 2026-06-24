"""Shared UI components and global CSS injection for DealScreen AI."""

import pandas as pd
import streamlit as st

from utils.formatters import compute_sensitivity_row, confidence_dot, extract_go_no_go, fmt_value

# ── Field / metric label maps ────────────────────────────────────────────────

FIELD_LABELS = {
    "property_name":        "Property Name",
    "location":             "Location",
    "asset_class":          "Asset Class",
    "units":                "Units / SF",
    "asking_price":         "Asking Price",
    "year_built":           "Year Built",
    "occupancy_pct":        "Occupancy %",
    "noi_t12":              "NOI (T-12)",
    "noi_proforma":         "NOI (Proforma)",
    "asking_cap_rate":      "Asking Cap Rate",
    "gross_potential_rent": "Gross Potential Rent",
}

METRIC_LABELS = {
    "cap_rate_inplace":  "Cap Rate (T-12)",
    "cap_rate_proforma": "Cap Rate (Proforma)",
    "dscr":              "DSCR",
    "debt_yield":        "Debt Yield",
    "cash_on_cash":      "Cash-on-Cash",
}

STATUS_BADGE = {
    "pass":    "🟢 Pass",
    "warn":    "🟡 Warn",
    "fail":    "🔴 Fail",
    "missing": "⚪ N/A",
}

_STATUS_BG = {
    "pass":    "#f0fdf4",
    "warn":    "#fefce8",
    "fail":    "#fef2f2",
    "missing": "#f8fafc",
}

PIPELINE_STAGES = [
    "Parser",
    "Extractor",
    "Underwriter",
    "Risk Flagger",
    "Market Research",
    "Report Writer",
]

# ── Premium CSS ───────────────────────────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400&display=swap');

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stSidebarContent"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.block-container {
  padding-top: 3.5rem !important;
  padding-bottom: 3rem !important;
}

[data-testid="stSidebar"] {
  border-right: 1px solid #E2E8F0;
}

/* ── Hero ─────────────────────────────────────────────────────────── */
.ds-hero { padding: 52px 0 36px; text-align: center; }

.ds-product-badge {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.09em; color: #1B3A6B;
  background: #EEF4FF; border: 1px solid #C7D9F8;
  padding: 5px 14px; border-radius: 24px; margin-bottom: 24px;
}

.ds-hero-title {
  font-size: clamp(2.2rem, 5vw, 3.6rem);
  font-weight: 900; color: #0F1B38;
  letter-spacing: -0.03em; line-height: 1.07; margin: 0 0 18px;
}
.ds-hero-accent { color: #1B3A6B; }

.ds-hero-sub {
  font-size: 17px; color: #64748B;
  max-width: 480px; margin: 0 auto 36px;
  line-height: 1.65;
}

/* ── How it works steps ───────────────────────────────────────────── */
.ds-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px; margin-top: 36px;
}
@media (max-width: 720px) { .ds-steps { grid-template-columns: 1fr; } }

.ds-step-card {
  background: #fff; border: 1px solid #E8EDF5;
  border-radius: 12px; padding: 28px 22px;
  box-shadow: 0 1px 3px rgba(15,27,56,.04);
}
.ds-step-num {
  width: 40px; height: 40px; border-radius: 10px;
  background: #1B3A6B; color: #fff;
  font-size: 16px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.ds-step-title { font-size: 15px; font-weight: 700; color: #0F1B38; margin-bottom: 8px; }
.ds-step-desc  { font-size: 13px; color: #64748B; line-height: 1.65; }

/* ── Page header ──────────────────────────────────────────────────── */
.ds-title-block {
  margin-bottom: 22px; padding-bottom: 16px;
  border-bottom: 1px solid #E8EDF5;
}
.ds-page-title {
  font-size: 22px; font-weight: 800; color: #0F1B38;
  letter-spacing: -0.02em; margin: 0 0 3px;
}
.ds-page-sub { font-size: 13px; color: #64748B; }

/* ── KPI row ──────────────────────────────────────────────────────── */
.ds-kpi-row {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 14px; margin: 20px 0;
}
@media (max-width: 900px) { .ds-kpi-row { grid-template-columns: repeat(2, 1fr); } }

.ds-kpi-card {
  background: #fff; border: 1px solid #E8EDF5;
  border-top: 3px solid #94A3B8;
  border-radius: 10px; padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(15,27,56,.04);
}
.ds-kpi-card.kpi-pass       { border-top-color: #16A34A; }
.ds-kpi-card.kpi-warn       { border-top-color: #D97706; }
.ds-kpi-card.kpi-fail       { border-top-color: #DC2626; }
.ds-kpi-card.kpi-strong     { border-top-color: #1B3A6B; }
.ds-kpi-card.kpi-borderline { border-top-color: #D97706; }
.ds-kpi-card.kpi-weak       { border-top-color: #DC2626; }
.ds-kpi-card.kpi-missing    { border-top-color: #94A3B8; }

.ds-kpi-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; color: #94A3B8; margin-bottom: 10px;
}
.ds-kpi-value {
  font-size: 24px; font-weight: 800; color: #0F1B38;
  line-height: 1; letter-spacing: -.01em; margin-bottom: 8px;
}
.ds-kpi-badge {
  display: inline-block; font-size: 10px; font-weight: 600;
  padding: 2px 8px; border-radius: 20px;
}
.badge-pass       { background: #DCFCE7; color: #15803D; }
.badge-warn       { background: #FEF3C7; color: #B45309; }
.badge-fail       { background: #FEE2E2; color: #B91C1C; }
.badge-missing    { background: #F1F5F9; color: #64748B; }
.badge-strong     { background: #DBEAFE; color: #1B3A6B; }
.badge-borderline { background: #FEF3C7; color: #B45309; }
.badge-weak       { background: #FEE2E2; color: #B91C1C; }

/* ── Score card ───────────────────────────────────────────────────── */
.ds-score-wrap {
  display: flex; align-items: center; gap: 28px;
  background: #fff; border: 1px solid #E8EDF5;
  border-radius: 12px; padding: 24px 28px;
  box-shadow: 0 2px 8px rgba(15,27,56,.07);
  margin-bottom: 20px; flex-wrap: wrap;
}
.ds-score-num {
  font-size: 56px; font-weight: 900; line-height: 1;
  letter-spacing: -0.03em;
}
.ds-score-num-sub { font-size: 20px; font-weight: 400; color: #94A3B8; }
.ds-score-pill { font-size: 14px; font-weight: 700; padding: 6px 18px; border-radius: 24px; }
.ds-score-expl { font-size: 13px; color: #64748B; max-width: 340px; line-height: 1.65; }

/* ── Pipeline bar ─────────────────────────────────────────────────── */
.ds-pipeline-bar {
  display: flex; align-items: flex-start;
  background: #fff; border: 1px solid #E8EDF5;
  border-radius: 10px; padding: 18px 24px 14px;
  overflow-x: auto; margin: 16px 0;
  box-shadow: 0 1px 3px rgba(15,27,56,.04);
}
.ds-pb-step {
  display: flex; flex-direction: column;
  align-items: center; gap: 6px;
  flex: 1; min-width: 70px;
}
.ds-pb-badge {
  width: 30px; height: 30px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 800;
  background: #EEF2F7; color: #94A3B8;
  border: 2px solid #E2E8F0;
}
.ds-pb-badge.pb-success { background: #DCFCE7; color: #15803D; border-color: #86EFAC; }
.ds-pb-badge.pb-error   { background: #FEE2E2; color: #B91C1C; border-color: #FCA5A5; }
.ds-pb-badge.pb-running { background: #EFF6FF; color: #1D4ED8; border-color: #93C5FD; }

.ds-pb-conn {
  flex: 0 0 auto; width: 20px; height: 2px;
  background: #E2E8F0; margin-top: 14px;
}
.ds-pb-conn.pc-done { background: #16A34A; }

.ds-pb-label {
  font-size: 9px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .05em;
  color: #94A3B8; text-align: center; white-space: nowrap;
}
.ds-pb-label.pl-success { color: #15803D; }
.ds-pb-label.pl-error   { color: #B91C1C; }
.ds-pb-label.pl-running { color: #1D4ED8; }

/* ── Risk flags ───────────────────────────────────────────────────── */
.ds-flag { border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; }
.ds-flag-critical {
  background: #FFF5F5; border: 1px solid #FED7D7;
  border-left: 4px solid #C53030;
}
.ds-flag-warning {
  background: #FFFBEB; border: 1px solid #FDE68A;
  border-left: 4px solid #D97706;
}
.ds-flag-info {
  background: #F0F9FF; border: 1px solid #BAE6FD;
  border-left: 4px solid #0284C7;
}
.ds-flag-title {
  font-size: 13px; font-weight: 700; color: #0F1B38; margin-bottom: 4px;
}
.ds-flag-detail { font-size: 13px; color: #475569; line-height: 1.6; }

/* ── Section heading ──────────────────────────────────────────────── */
.ds-section-head {
  display: flex; align-items: center; gap: 10px;
  margin: 28px 0 14px; padding-bottom: 10px;
  border-bottom: 1px solid #EEF2F7;
}
.ds-section-num {
  width: 26px; height: 26px; border-radius: 6px;
  background: #1B3A6B; color: #fff;
  font-size: 11px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.ds-section-text {
  font-size: 15px; font-weight: 700; color: #0F1B38; letter-spacing: -0.01em;
}

/* ── Empty state ──────────────────────────────────────────────────── */
.ds-empty {
  text-align: center; padding: 56px 40px;
  background: #fff; border: 1px dashed #CBD5E1;
  border-radius: 12px; margin: 20px 0;
}
.ds-empty-icon  { font-size: 40px; margin-bottom: 16px; }
.ds-empty-title { font-size: 18px; font-weight: 700; color: #0F1B38; margin-bottom: 8px; }
.ds-empty-sub   { font-size: 13px; color: #64748B; max-width: 340px; margin: 0 auto; line-height: 1.6; }

/* ── Memo card ────────────────────────────────────────────────────── */
.ds-memo-wrap {
  background: #fff; border: 1px solid #E8EDF5;
  border-radius: 12px; padding: 32px 36px;
  box-shadow: 0 1px 4px rgba(15,27,56,.05); line-height: 1.7;
}

/* ── Compare winner badge ─────────────────────────────────────────── */
.ds-winner-badge {
  display: inline-flex; align-items: center; gap: 4px;
  background: #1B3A6B; color: #fff;
  font-size: 11px; font-weight: 700;
  padding: 3px 10px; border-radius: 20px; margin-left: 8px;
}

/* ── Info strip (settings / home) ────────────────────────────────── */
.ds-info-card {
  background: #fff; border: 1px solid #E8EDF5;
  border-radius: 10px; padding: 22px 24px;
  box-shadow: 0 1px 3px rgba(15,27,56,.04);
  margin-bottom: 14px;
}
.ds-info-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; color: #94A3B8; margin-bottom: 6px;
}
.ds-info-value { font-size: 15px; font-weight: 600; color: #0F1B38; }
.ds-info-sub   { font-size: 12px; color: #64748B; margin-top: 4px; }

/* ── IC Summary Strip ─────────────────────────────────────────────── */
.ds-ic-strip {
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  border-radius: 8px; padding: 10px 18px; margin-bottom: 12px;
}
.ds-ic-strip-go   { background: #f0fdf4; border: 1px solid #86EFAC; border-left: 4px solid #16A34A; }
.ds-ic-strip-nogo { background: #fef2f2; border: 1px solid #FCA5A5; border-left: 4px solid #DC2626; }
.ds-ic-strip-need { background: #fefce8; border: 1px solid #FDE68A; border-left: 4px solid #D97706; }
.ds-ic-label   { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #94A3B8; }
.ds-ic-rec     { font-size: 14px; font-weight: 800; }
.ds-ic-score   { font-size: 12px; font-weight: 500; color: #0F1B38; }
.ds-ic-flag    { font-size: 12px; color: #475569; }
.ds-ic-divider { color: #CBD5E1; font-size: 14px; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def source_tag(label: str) -> None:
    """Render a small gray source-attribution caption (e.g. 'Source: OM p.14')."""
    st.markdown(
        f'<span style="font-size:11px;color:#94A3B8;font-weight:500;">'
        f'📄 {label}</span>',
        unsafe_allow_html=True,
    )


# ── Layout helpers ────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""<div class="ds-title-block">
          <div class="ds-page-title">{title}</div>
          <div class="ds-page-sub">{subtitle}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def section_header(num: str, title: str) -> None:
    st.markdown(
        f"""<div class="ds-section-head">
          <div class="ds-section-num">{num}</div>
          <div class="ds-section-text">{title}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""<div class="ds-empty">
          <div class="ds-empty-icon">{icon}</div>
          <div class="ds-empty-title">{title}</div>
          <div class="ds-empty-sub">{subtitle}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ── Pipeline bar ─────────────────────────────────────────────────────────────

def render_pipeline_bar(stage_states: dict) -> None:
    """Render the 6-stage visual pipeline bar. stage_states maps stage name → 'running'|'success'|'error'|''."""
    items = []
    for i, name in enumerate(PIPELINE_STAGES):
        state     = stage_states.get(name, "")
        is_last   = i == len(PIPELINE_STAGES) - 1
        badge_cls = f"ds-pb-badge pb-{state}" if state else "ds-pb-badge"
        label_cls = f"ds-pb-label pl-{state}" if state else "ds-pb-label"
        icon      = "✓" if state == "success" else ("✗" if state == "error" else str(i + 1))
        short     = name.replace(" ", "&nbsp;")

        step_html = (
            f'<div class="ds-pb-step">'
            f'  <div class="{badge_cls}">{icon}</div>'
            f'  <div class="{label_cls}">{short}</div>'
            f'</div>'
        )
        if not is_last:
            conn_cls  = "ds-pb-conn pc-done" if state == "success" else "ds-pb-conn"
            step_html += f'<div class="{conn_cls}"></div>'
        items.append(step_html)

    st.markdown(
        f'<div class="ds-pipeline-bar">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


# ── KPI row ───────────────────────────────────────────────────────────────────

def _kpi_card_html(label: str, value: str, badge_text: str, css_class: str) -> str:
    badge = (
        f'<div class="ds-kpi-badge badge-{css_class}">{badge_text}</div>'
        if badge_text else ""
    )
    return (
        f'<div class="ds-kpi-card kpi-{css_class}">'
        f'  <div class="ds-kpi-label">{label}</div>'
        f'  <div class="ds-kpi-value">{value}</div>'
        f'  {badge}'
        f'</div>'
    )


def render_kpi_row(uw_live: dict, extracted: dict) -> None:
    if not uw_live:
        return

    ds      = uw_live.get("deal_score", {})
    metrics = uw_live.get("metrics", {})

    # Deal score card
    score     = ds.get("score")
    label     = ds.get("label", "Weak")
    score_str = (
        f'{score:.0f}<span style="font-size:14px;font-weight:400;color:#94A3B8"> / 100</span>'
        if score is not None else "—"
    )
    score_css = label.lower().replace(" ", "") if label else "weak"
    score_card = _kpi_card_html("Deal Score", score_str, label, score_css)

    # Cap rate card
    cap_m    = metrics.get("cap_rate_inplace", {})
    cap_card = _kpi_card_html(
        "Cap Rate (T-12)", cap_m.get("formatted", "—"),
        cap_m.get("benchmark", ""), cap_m.get("status", "missing"),
    )

    # DSCR card
    dscr_m    = metrics.get("dscr", {})
    dscr_card = _kpi_card_html(
        "DSCR", dscr_m.get("formatted", "—"),
        dscr_m.get("benchmark", ""), dscr_m.get("status", "missing"),
    )

    # Occupancy card
    occ_entry = extracted.get("occupancy_pct", {}) if extracted else {}
    occ_val   = occ_entry.get("value") if isinstance(occ_entry, dict) else None
    occ_str   = f"{occ_val:.1f}%" if occ_val is not None else "—"
    occ_st    = (
        "pass" if (occ_val or 0) >= 90
        else ("warn" if (occ_val or 0) >= 80 else "fail")
    ) if occ_val is not None else "missing"
    occ_card = _kpi_card_html("Occupancy", occ_str, "≥ 90% lender min", occ_st)

    st.markdown(
        f'<div class="ds-kpi-row">{score_card}{cap_card}{dscr_card}{occ_card}</div>',
        unsafe_allow_html=True,
    )


# ── Deal score card ───────────────────────────────────────────────────────────

_SCORE_PALETTES = {
    "Strong":     ("color:#155724", "background:#DCFCE7;color:#15803D"),
    "Borderline": ("color:#92400E", "background:#FEF3C7;color:#92400E"),
    "Weak":       ("color:#991B1B", "background:#FEE2E2;color:#991B1B"),
}


def render_deal_score_card(ds: dict) -> None:
    if not ds or ds.get("score") is None:
        return
    score       = ds["score"]
    label       = ds.get("label", "Weak")
    explanation = ds.get("explanation", "")
    num_style, pill_style = _SCORE_PALETTES.get(label, _SCORE_PALETTES["Weak"])
    st.markdown(
        f"""<div class="ds-score-wrap">
          <div>
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;
                        letter-spacing:.08em;color:#94A3B8;margin-bottom:6px;">Deal Score</div>
            <div class="ds-score-num" style="{num_style}">
              {score:.0f}<span class="ds-score-num-sub"> / 100</span>
            </div>
          </div>
          <div class="ds-score-pill" style="{pill_style}">{label}</div>
          <div class="ds-score-expl">{explanation}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ── Extracted data table ──────────────────────────────────────────────────────

def render_extraction(extracted: dict) -> None:
    if "extraction_error" in extracted:
        st.error(f"Extraction failed: {extracted['extraction_error']}")
        if "raw_response" in extracted:
            with st.expander("Raw LLM response"):
                st.code(extracted["raw_response"])
        return

    missing = [
        FIELD_LABELS.get(k, k)
        for k, v in extracted.items()
        if isinstance(v, dict) and v.get("flag") == "missing"
    ]
    if missing:
        st.warning(f"Fields not found in document: **{', '.join(missing)}**")

    rows = []
    for field, label in FIELD_LABELS.items():
        entry = extracted.get(field, {})
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        conf  = entry.get("confidence", 0)
        page  = entry.get("source_page")
        flag  = entry.get("flag")
        rows.append({
            "Field":       label,
            "Value":       fmt_value(field, value),
            "Confidence":  f"{confidence_dot(conf)} {conf}%",
            "Source Page": f"p.{page}" if page else "—",
            "_conf":       conf,
            "_flag":       flag,
        })

    df   = pd.DataFrame(rows)
    disp = df[["Field", "Value", "Confidence", "Source Page"]].copy()

    def row_style(row):
        flag = df.loc[row.name, "_flag"]
        conf = df.loc[row.name, "_conf"]
        if flag == "missing": return ["background-color: #fefce8"] * len(row)
        if conf >= 80:        return ["background-color: #f0fdf4"] * len(row)
        if conf >= 50:        return ["background-color: #fefce8"] * len(row)
        return ["background-color: #fef2f2"] * len(row)

    st.dataframe(disp.style.apply(row_style, axis=1), use_container_width=True, hide_index=True)
    st.caption("🟢 ≥80% confidence · 🟡 50–79% · 🔴 <50% · Yellow background = field not found in document")


# ── Underwriter metrics table ─────────────────────────────────────────────────

def render_underwriter(uw: dict) -> None:
    if uw.get("underwriter_error"):
        st.error(f"Underwriter error: {uw['underwriter_error']}")
        return

    loan = uw["loan_assumptions"]
    st.caption(
        f"**{loan['ltv']*100:.0f}% LTV** · "
        f"**{loan['rate']*100:.1f}% fixed** · "
        f"**{loan['amortization_years']}-yr amortization** · "
        f"**{loan.get('hold_period_years', 5)}-yr hold** · "
        f"Loan **${loan['loan_amount']:,.0f}** · "
        f"Equity **${loan['equity_invested']:,.0f}** · "
        f"Ann. Debt Service **${loan['annual_debt_service']:,.0f}**"
    )

    rows = []
    for key, label in METRIC_LABELS.items():
        m      = uw["metrics"].get(key, {})
        status = m.get("status", "missing")
        rows.append({
            "Metric":    label,
            "Value":     m.get("formatted", "—"),
            "Formula":   m.get("formula_used", "—"),
            "Benchmark": m.get("benchmark", "—"),
            "Status":    STATUS_BADGE.get(status, status),
            "_status":   status,
        })

    em = uw["equity_multiple"]
    rows.append({
        "Metric":    "Equity Multiple",
        "Value":     f"{em['value']:.1f}x" if em.get("value") else "—",
        "Formula":   "Exit Proceeds / Total Equity",
        "Benchmark": "Needs hold period",
        "Status":    "⚪ Needs Input",
        "_status":   "missing",
    })

    df   = pd.DataFrame(rows)
    disp = df[["Metric", "Value", "Formula", "Benchmark", "Status"]].copy()

    def row_style(row):
        bg = _STATUS_BG.get(df.loc[row.name, "_status"], "#f8fafc")
        return [f"background-color: {bg}"] * len(row)

    st.dataframe(disp.style.apply(row_style, axis=1), use_container_width=True, hide_index=True)


# ── Risk flags ────────────────────────────────────────────────────────────────

def render_risk_flags(risk: dict) -> None:
    if risk.get("flagger_error"):
        st.error(f"Risk flagger error: {risk['flagger_error']}")
        return

    flags     = risk.get("flags", [])
    triggered = [f for f in flags if f["triggered"]]
    clear     = [f for f in flags if not f["triggered"]]

    if risk["critical_count"] > 0:
        st.error(f"**{risk['critical_count']} critical flag(s)** — must review before proceeding.")
    elif risk["triggered_count"] > 0:
        st.warning(f"**{risk['triggered_count']} flag(s) triggered** — review before closing.")
    else:
        st.success("No risk flags triggered.")

    for flag in triggered:
        sev = flag["severity"]
        cls = (
            "ds-flag-critical" if sev == "critical"
            else ("ds-flag-warning" if sev == "warning" else "ds-flag-info")
        )
        icon = "🚨" if sev == "critical" else ("⚠️" if sev == "warning" else "ℹ️")
        sev_label = f'<span style="font-size:10px;font-weight:600;opacity:.55;margin-left:4px;">{sev.upper()}</span>'
        st.markdown(
            f"""<div class="ds-flag {cls}">
              <div class="ds-flag-title">{icon} {flag['flag_name']}{sev_label}</div>
              <div class="ds-flag-detail">{flag['detail']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    if clear:
        with st.expander(f"✅ {len(clear)} checks passed"):
            for flag in clear:
                st.markdown(f"**{flag['flag_name']}** — {flag['detail']}")


# ── Market research ───────────────────────────────────────────────────────────

def render_market_research(market: dict) -> None:
    if market.get("researcher_error"):
        st.error(f"Market research error: {market['researcher_error']}")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Cap Rate Benchmark", market.get("cap_rate_benchmark") or "—")
    trend     = market.get("rent_growth_trend", {})
    direction = trend.get("direction") or "—"
    dir_icon  = {"positive": "📈", "flat": "➡️", "negative": "📉"}.get(direction, "")
    col2.metric("Rent Growth Trend", f"{dir_icon} {direction.capitalize()}")
    positioning = market.get("deal_positioning") or "—"
    pos_icon    = {"below market": "🔻", "at market": "🔹", "above market": "🔺"}.get(positioning, "")
    col3.metric("Deal Positioning", f"{pos_icon} {positioning.title()}")

    if market.get("submarket_summary"):
        st.info(market["submarket_summary"])
    if trend.get("reason"):
        st.caption(f"Rent trend rationale: {trend['reason']}")
    if market.get("footer"):
        st.caption(f"_{market['footer']}_")


# ── IC Summary Strip ──────────────────────────────────────────────────────────

def render_ic_summary_strip(uw_live: dict, risk: dict, report: dict) -> None:
    """Compact one-line IC-ready banner: Recommendation · Deal Score · Top Flag."""
    ds    = uw_live.get("deal_score", {})
    score = ds.get("score")
    label = ds.get("label", "Weak")  # Strong | Borderline | Weak

    # Derive recommendation from IC Memo when available, else from score/flags
    memo_md = (report or {}).get("memo_markdown") or ""
    writer_ok = memo_md and not (report or {}).get("writer_error")
    if writer_ok:
        raw = extract_go_no_go(memo_md)
        recommendation = {"Go": "GO", "No-Go": "NO-GO", "Conditional Go": "NEED INFO"}.get(
            raw, "NEED INFO"
        )
    else:
        flags = (risk or {}).get("flags", [])
        has_critical = any(f.get("severity") == "critical" and f.get("triggered") for f in flags)
        if has_critical or label == "Weak":
            recommendation = "NO-GO"
        elif label == "Strong":
            recommendation = "GO"
        else:
            recommendation = "NEED INFO"

    # Highest-severity triggered flag
    flags     = (risk or {}).get("flags", [])
    triggered = [f for f in flags if f.get("triggered")]
    _sev_rank = {"critical": 0, "warning": 1, "info": 2}
    top_flag  = min(triggered, key=lambda f: _sev_rank.get(f.get("severity", "info"), 2), default=None)

    strip_cls = {"GO": "ds-ic-strip-go", "NO-GO": "ds-ic-strip-nogo"}.get(
        recommendation, "ds-ic-strip-need"
    )
    rec_color = {"GO": "#15803D", "NO-GO": "#B91C1C"}.get(recommendation, "#B45309")
    score_str = f"{score:.0f} / 100" if score is not None else "—"

    flag_html = ""
    if top_flag:
        sev   = top_flag.get("severity", "info")
        icons = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
        flag_html = (
            f'<span class="ds-ic-divider">|</span>'
            f'<span class="ds-ic-flag">{icons.get(sev, "ℹ️")} '
            f'{sev.capitalize()}: {top_flag.get("flag_name", "")}</span>'
        )

    st.markdown(
        f"""<div class="ds-ic-strip {strip_cls}">
          <span class="ds-ic-label">Recommendation</span>
          <span class="ds-ic-rec" style="color:{rec_color};">{recommendation}</span>
          <span class="ds-ic-divider">|</span>
          <span class="ds-ic-score">Deal Score: <strong>{score_str}</strong></span>
          {flag_html}
        </div>""",
        unsafe_allow_html=True,
    )


# ── Sensitivity Analysis Table ────────────────────────────────────────────────

def render_sensitivity_table(extracted: dict, assumptions: dict) -> None:
    """DSCR × Cap Rate sensitivity table across Base / Downside / Upside scenarios."""
    if not extracted:
        return

    def _get(field):
        e = extracted.get(field, {})
        return e.get("value") if isinstance(e, dict) else None

    asking_price = _get("asking_price")
    noi_proforma = _get("noi_proforma")
    ltv      = assumptions.get("ltv", 0.70)
    rate     = assumptions.get("rate", 0.065)
    am_years = assumptions.get("amortization_years", 30)

    st.divider()
    st.markdown("#### Sensitivity Analysis")

    if asking_price is None or noi_proforma is None:
        st.info(
            "Sensitivity requires proforma NOI. "
            "Ensure the OM includes proforma financials for this section to populate."
        )
        return

    scenarios = [
        ("Base Case", ltv,         rate,         noi_proforma),
        ("Downside",  ltv + 0.05,  rate + 0.005, noi_proforma * 0.90),
        ("Upside",    ltv - 0.05,  rate - 0.005, noi_proforma * 1.10),
    ]

    rows = []
    for name, s_ltv, s_rate, s_noi in scenarios:
        dscr, cap = compute_sensitivity_row(asking_price, s_noi, s_ltv, s_rate, am_years)
        rows.append({
            "Scenario":  name,
            "LTV":       f"{s_ltv * 100:.0f}%",
            "Int. Rate": f"{s_rate * 100:.1f}%",
            "NOI":       f"${s_noi:,.0f}",
            "DSCR":      f"{dscr:.2f}x" if dscr is not None else "N/A",
            "Cap Rate":  f"{cap:.2f}%"   if cap  is not None else "N/A",
        })

    df = pd.DataFrame(rows)

    def _row_style(row):
        bg = {"Upside": "#f0fdf4", "Downside": "#fef2f2"}.get(df.loc[row.name, "Scenario"], "#EFF3F8")
        return [f"background-color:{bg}"] * len(row)

    st.dataframe(df.style.apply(_row_style, axis=1), use_container_width=True, hide_index=True)
    st.caption(
        "Downside: LTV +5%, rate +0.5%, NOI ×0.90 · "
        "Upside: LTV −5%, rate −0.5%, NOI ×1.10 · "
        "Base Case uses current sidebar assumptions."
    )


# ── Stress Test – Base / Bull / Bear (Feature 1) ─────────────────────────────

def render_stress_test(extracted: dict, assumptions: dict) -> None:
    """Stress-test table directly below the sensitivity table."""
    if not extracted:
        return

    def _get(field):
        e = extracted.get(field, {})
        return e.get("value") if isinstance(e, dict) else None

    asking_price = _get("asking_price")
    noi_base     = _get("noi_t12") or _get("noi_proforma")
    cap_raw      = _get("asking_cap_rate")   # in % (e.g. 5.25)

    if asking_price is None or noi_base is None:
        st.info(
            "Stress test requires Asking Price and T-12 NOI. "
            "Ensure the OM includes these fields."
        )
        return

    ltv      = assumptions.get("ltv", 0.70)
    rate     = assumptions.get("rate", 0.065)
    am_years = assumptions.get("amortization_years", 30)

    # Fall back to implied cap rate if not in extracted data
    cap_base = cap_raw if cap_raw is not None else (noi_base / asking_price * 100)

    # Base: current assumptions · Bull: NOI +5%, exit cap −25 bps · Bear: NOI −10%, exit cap +75 bps
    scenario_defs = [
        ("Base", noi_base,         cap_base),
        ("Bull", noi_base * 1.05,  cap_base - 0.25),
        ("Bear", noi_base * 0.90,  cap_base + 0.75),
    ]

    scenario_vals = []
    for name, s_noi, s_cap_pct in scenario_defs:
        s_cap_pct = max(s_cap_pct, 0.50)          # floor at 50 bps
        implied   = s_noi / (s_cap_pct / 100)
        dscr, _   = compute_sensitivity_row(asking_price, s_noi, ltv, rate, am_years)
        scenario_vals.append((name, s_noi, s_cap_pct, dscr, implied))

    rows = [
        {
            "Scenario":      name,
            "NOI":           f"${s_noi:,.0f}",
            "Exit Cap Rate": f"{s_cap_pct:.2f}%",
            "DSCR":          f"{dscr:.2f}x" if dscr is not None else "N/A",
            "Implied Value": f"${implied:,.0f}",
        }
        for name, s_noi, s_cap_pct, dscr, implied in scenario_vals
    ]

    df = pd.DataFrame(rows)

    def _row_style(row):
        bg = {"Bull": "#f0fdf4", "Bear": "#fef2f2"}.get(df.loc[row.name, "Scenario"], "#EFF3F8")
        return [f"background-color:{bg}"] * len(row)

    st.divider()
    st.markdown("#### Stress Test – Base / Bull / Bear")
    st.dataframe(df.style.apply(_row_style, axis=1), use_container_width=True, hide_index=True)
    st.caption(
        "Base: pipeline assumptions · "
        "Bull: NOI +5%, exit cap −25 bps · "
        "Bear: NOI −10%, exit cap +75 bps · "
        "DSCR recomputed at current sidebar loan assumptions."
    )

    chart_df = pd.DataFrame(
        {"Implied Value ($)": [v[4] for v in scenario_vals]},
        index=[v[0] for v in scenario_vals],
    )
    st.bar_chart(chart_df, use_container_width=True)


# ── IRR & Equity Multiple (Feature 3) ────────────────────────────────────────

def compute_simple_irr_and_multiple(
    purchase_price: float,
    year1_noi: float,
    noi_growth_rate: float = 0.025,  # 2.5% annual NOI growth (conservative multifamily assumption)
    exit_cap_rate: float = 0.055,    # exit cap in decimal (e.g. 0.055 = 5.5%)
    hold_years: int = 5,
):
    """Unlevered IRR and equity multiple using a constant-growth model.

    CF_0 = -purchase_price
    CF_t = NOI_1 × (1+g)^(t-1)  for t = 1 … hold_years-1
    CF_hold = NOI_hold + NOI_hold / exit_cap_rate  (operating CF + terminal value)
    """
    if not purchase_price or not year1_noi or not exit_cap_rate:
        return None, None

    cfs = [-purchase_price]
    for t in range(1, hold_years + 1):
        noi_t = year1_noi * (1 + noi_growth_rate) ** (t - 1)
        terminal = (noi_t / exit_cap_rate) if t == hold_years else 0.0
        cfs.append(noi_t + terminal)

    equity_multiple = sum(cfs[1:]) / purchase_price

    def _npv(r: float) -> float:
        return sum(c / (1 + r) ** t for t, c in enumerate(cfs))

    try:
        lo, hi = -0.90, 10.0
        if _npv(lo) * _npv(hi) > 0:
            return None, equity_multiple
        for _ in range(200):
            mid = (lo + hi) / 2
            if _npv(mid) > 0:
                lo = mid
            else:
                hi = mid
        irr = (lo + hi) / 2
    except Exception:
        irr = None

    return irr, equity_multiple


def render_irr_multiple_kpi(
    purchase_price: float,
    year1_noi: float,
    exit_cap_rate: float,
    hold_years: int = 5,
) -> None:
    """Two KPI cards: estimated unlevered IRR and equity multiple."""
    irr, em = compute_simple_irr_and_multiple(
        purchase_price, year1_noi, exit_cap_rate=exit_cap_rate, hold_years=hold_years
    )

    irr_str = f"{irr * 100:.1f}%" if irr is not None else "—"
    em_str  = f"{em:.2f}x"        if em  is not None else "—"

    irr_css = (
        "pass" if (irr or 0) >= 0.07 else
        "warn" if (irr or 0) >= 0.05 else
        "fail"
    ) if irr is not None else "missing"

    em_css = (
        "pass" if (em or 0) >= 1.50 else
        "warn" if (em or 0) >= 1.20 else
        "fail"
    ) if em is not None else "missing"

    irr_card = _kpi_card_html(
        f"Est. {hold_years}-Yr IRR (Unlevered)", irr_str, "Target ≥ 7%", irr_css
    )
    em_card = _kpi_card_html("Est. Equity Multiple", em_str, "Target ≥ 1.5x", em_css)

    st.markdown(
        f'<div class="ds-kpi-row" style="grid-template-columns:repeat(2,1fr);max-width:560px;">'
        f'{irr_card}{em_card}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Pipeline Reliability (Settings page) ─────────────────────────────────────

def render_pipeline_reliability() -> None:
    """Session runtime metrics and hallucination guardrail summary for the Settings page."""
    run_history = st.session_state.get("run_history", [])

    # ── Section header ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """<div style="font-size:11px;font-weight:700;text-transform:uppercase;
                      letter-spacing:.08em;color:#94A3B8;margin-bottom:12px;">
          Pipeline Reliability
        </div>""",
        unsafe_allow_html=True,
    )

    # ── A) Runtime Metrics ─────────────────────────────────────────────────────
    total     = len(run_history)
    complete  = sum(1 for r in run_history if r.get("status") == "complete")
    incomplete = total - complete
    durations = [r["duration_s"] for r in run_history if r.get("duration_s") is not None]
    avg_dur   = sum(durations) / len(durations) if durations else None
    avg_str   = f"{avg_dur:.0f}s" if avg_dur is not None else "—"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""<div class="ds-info-card">
              <div class="ds-info-label">Deals Screened (Session)</div>
              <div class="ds-info-value">{total}</div>
              <div class="ds-info-sub">Total pipeline runs this session</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="ds-info-card">
              <div class="ds-info-label">Avg Pipeline Duration</div>
              <div class="ds-info-value">{avg_str}</div>
              <div class="ds-info-sub">Parser → Report Writer end-to-end</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""<div class="ds-info-card">
              <div class="ds-info-label">Data Completeness</div>
              <div class="ds-info-value">{complete} complete · {incomplete} incomplete</div>
              <div class="ds-info-sub">Critical fields: Asking Price + T-12 NOI</div>
            </div>""",
            unsafe_allow_html=True,
        )

    if run_history:
        rows = []
        for r in run_history[-10:]:
            ts  = (r.get("timestamp") or "")[:19].replace("T", " ")
            dur = f"{r['duration_s']:.0f}s" if r.get("duration_s") is not None else "—"
            sc  = f"{r['score']:.0f} / 100" if r.get("score") is not None else "—"
            rows.append({
                "Timestamp": ts,
                "Deal":      r.get("deal_name", "Unknown"),
                "Score":     sc,
                "Duration":  dur,
                "Status":    "✅ Complete" if r.get("status") == "complete" else "⚠️ Missing Critical Fields",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No deals screened this session. Upload an OM on the Screen Deal page to begin.")

    # ── B) Hallucination Guardrail Summary ────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """<div style="font-size:11px;font-weight:700;text-transform:uppercase;
                      letter-spacing:.08em;color:#94A3B8;margin-bottom:12px;">
          Hallucination Guardrails
        </div>""",
        unsafe_allow_html=True,
    )
    _badge = (
        "font-size:12px;font-weight:700;padding:2px 10px;border-radius:12px;"
        "white-space:nowrap;background:#FEF3C7;color:#B45309;"
    )
    _row_sep = "display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid #EEF2F7;"
    _row_last = "display:flex;align-items:flex-start;gap:12px;padding:10px 0;"
    _body = "font-size:13px;color:#475569;line-height:1.6;"
    st.markdown(
        f"""<div class="ds-info-card">
          <div class="ds-info-label">What the Agent Does When Data Is Missing</div>
          <div style="margin-top:10px;">
            <div style="{_row_sep}">
              <span style="{_badge}">T-12 NOI Missing</span>
              <span style="{_body}">DSCR is not calculated. Displayed as "—" in all metric tables.
              The IC Memo notes that T-12 NOI was unavailable and omits DSCR from the underwriting summary.</span>
            </div>
            <div style="{_row_sep}">
              <span style="{_badge}">Year Built Missing</span>
              <span style="{_body}">CapEx risk is flagged as unknown. The Risk Flagger raises a warning
              flag for potential deferred maintenance exposure since asset age cannot be assessed.</span>
            </div>
            <div style="{_row_last}">
              <span style="{_badge}">Occupancy Missing</span>
              <span style="{_body}">A stabilization risk flag is raised. Underwriting proceeds with
              available NOI data, but occupancy-dependent metrics are marked unavailable in the output.</span>
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
