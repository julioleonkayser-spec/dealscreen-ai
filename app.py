"""PD Hackathon — AI Deal Screening Agent | Streamlit Web UI"""

import hashlib
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # local dev only; no-ops on Streamlit Cloud where .env doesn't exist

sys.path.insert(0, str(Path(__file__).parent))

from agents.extractor import extract_financials
from agents.market_researcher import research_market
from agents.parser import parse_pdf
from agents.report_writer import write_report
from agents.risk_flagger import flag_risks
from agents.underwriter import underwrite
from utils.excel_export import export_excel_model
from utils.history import append_history_entry, load_history
from utils.pdf_export import generate_pdf_bytes

st.set_page_config(
    page_title="AI Deal Screening Agent",
    page_icon="🏢",
    layout="wide",
)

AGENT_NAMES = [
    "1. Parser",
    "2. Extractor",
    "3. Underwriter",
    "4. Risk Flagger",
    "5. Market Research",
    "6. Report Writer",
]

FIELD_LABELS = {
    "property_name":      "Property Name",
    "location":           "Location",
    "asset_class":        "Asset Class",
    "units":              "Units / SF",
    "asking_price":       "Asking Price",
    "year_built":         "Year Built",
    "occupancy_pct":      "Occupancy %",
    "noi_t12":            "NOI (T-12)",
    "noi_proforma":       "NOI (Proforma)",
    "asking_cap_rate":    "Asking Cap Rate",
    "gross_potential_rent": "Gross Potential Rent",
}

DOLLAR_FIELDS = {"asking_price", "noi_t12", "noi_proforma", "gross_potential_rent"}
PCT_FIELDS    = {"occupancy_pct", "asking_cap_rate"}

METRIC_LABELS = {
    "cap_rate_inplace":  "Cap Rate (T-12)",
    "cap_rate_proforma": "Cap Rate (Proforma)",
    "dscr":              "DSCR",
    "debt_yield":        "Debt Yield",
    "cash_on_cash":      "Cash-on-Cash",
}

STATUS_BADGE = {"pass": "🟢 Pass", "warn": "🟡 Warn", "fail": "🔴 Fail", "missing": "⚪ N/A"}
STATUS_BG    = {"pass": "#d4edda", "warn": "#fff3cd", "fail": "#f8d7da", "missing": "#f8f9fa"}

SCORE_PALETTE = {
    "Strong":    {"bg": "#d4edda", "text": "#155724", "pill": "#28a745"},
    "Borderline": {"bg": "#fff3cd", "text": "#856404", "pill": "#e6a817"},
    "Weak":      {"bg": "#f8d7da", "text": "#721c24", "pill": "#dc3545"},
}


# ── Formatting helpers ───────────────────────────────────────────────────────

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


def confidence_dot(conf: int) -> str:
    if conf >= 80:
        return "🟢"
    if conf >= 50:
        return "🟡"
    return "🔴"


# ── Section renderers ────────────────────────────────────────────────────────

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
        st.warning(f"⚠️ Fields not found: **{', '.join(missing)}**")

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
        if flag == "missing": return ["background-color: #fff3cd"] * len(row)
        if conf >= 80:        return ["background-color: #d4edda"] * len(row)
        if conf >= 50:        return ["background-color: #fff3cd"] * len(row)
        return ["background-color: #f8d7da"] * len(row)

    st.dataframe(disp.style.apply(row_style, axis=1), use_container_width=True, hide_index=True)
    st.caption("🟢 ≥80% confidence · 🟡 50–79% · 🔴 <50% · Yellow = not found")


def render_underwriter(uw: dict) -> None:
    if uw.get("underwriter_error"):
        st.error(f"Underwriter error: {uw['underwriter_error']}")
        return

    loan = uw["loan_assumptions"]
    st.caption(
        f"Assumptions: **{loan['ltv']*100:.0f}% LTV** · "
        f"**{loan['rate']*100:.1f}% fixed** · "
        f"**{loan['amortization_years']}-yr am** · "
        f"**{loan.get('hold_period_years', 5)}-yr hold** · "
        f"Loan **${loan['loan_amount']:,.0f}** · "
        f"Equity **${loan['equity_invested']:,.0f}** · "
        f"Ann. DS **${loan['annual_debt_service']:,.0f}**"
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
        bg = STATUS_BG.get(df.loc[row.name, "_status"], "#f8f9fa")
        return [f"background-color: {bg}"] * len(row)

    st.dataframe(disp.style.apply(row_style, axis=1), use_container_width=True, hide_index=True)


def render_risk_flags(risk: dict) -> None:
    if risk.get("flagger_error"):
        st.error(f"Risk flagger error: {risk['flagger_error']}")
        return

    flags     = risk.get("flags", [])
    triggered = [f for f in flags if f["triggered"]]
    clear     = [f for f in flags if not f["triggered"]]

    if risk["critical_count"] > 0:
        st.error(f"🚨 **{risk['critical_count']} critical flag(s)** — review before proceeding.")
    elif risk["triggered_count"] > 0:
        st.warning(f"⚠️ **{risk['triggered_count']} warning(s)** — review before closing.")
    else:
        st.success("✅ No risk flags triggered.")

    for flag in triggered:
        sev  = flag["severity"]
        icon = "🚨" if sev == "critical" else "⚠️"
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{icon} {flag['flag_name']}**")
            c2.markdown(
                f"<span style='color:{'red' if sev=='critical' else 'orange'};font-weight:bold'>"
                f"{sev.upper()}</span>",
                unsafe_allow_html=True,
            )
            st.caption(flag["detail"])

    if clear:
        with st.expander(f"✅ {len(clear)} flag(s) not triggered"):
            for flag in clear:
                st.markdown(f"**{flag['flag_name']}** — {flag['detail']}")


def render_market_research(market: dict) -> None:
    if market.get("researcher_error"):
        st.error(f"Market research error: {market['researcher_error']}")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Cap Rate Benchmark", market.get("cap_rate_benchmark") or "—")
    trend     = market.get("rent_growth_trend", {})
    direction = trend.get("direction") or "—"
    dir_icon  = {"positive": "📈", "flat": "➡️", "negative": "📉"}.get(direction, "")
    col2.metric("Rent Growth", f"{dir_icon} {direction.capitalize()}")
    positioning = market.get("deal_positioning") or "—"
    pos_icon    = {"below market": "🔻", "at market": "🔹", "above market": "🔺"}.get(positioning, "")
    col3.metric("Deal Positioning", f"{pos_icon} {positioning.title()}")

    if market.get("submarket_summary"):
        st.info(market["submarket_summary"])
    if trend.get("reason"):
        st.caption(f"Rent trend rationale: {trend['reason']}")
    if market.get("footer"):
        st.caption(f"_{market['footer']}_")


def render_deal_score(ds: dict) -> None:
    """Prominent score card above the data tables."""
    if not ds or ds.get("score") is None:
        return

    score = ds["score"]
    label = ds.get("label", "Weak")
    explanation = ds.get("explanation", "")
    palette = SCORE_PALETTE.get(label, SCORE_PALETTE["Weak"])

    st.markdown(
        f"""
        <div style="
            background:{palette['bg']};
            border-radius:12px;
            padding:20px 28px;
            margin-bottom:20px;
            display:flex;
            align-items:center;
            gap:24px;
            flex-wrap:wrap;
        ">
            <div>
                <div style="font-size:11px;color:{palette['text']};font-weight:700;
                            text-transform:uppercase;letter-spacing:0.07em;margin-bottom:2px;">
                    Deal Score
                </div>
                <div style="font-size:52px;font-weight:800;color:{palette['text']};line-height:1;">
                    {score:.0f}
                    <span style="font-size:22px;font-weight:400;opacity:0.7;">/ 100</span>
                </div>
            </div>
            <div style="
                background:{palette['pill']};color:#fff;
                padding:6px 20px;border-radius:20px;
                font-weight:700;font-size:15px;white-space:nowrap;
            ">{label}</div>
            <div style="font-size:12px;color:{palette['text']};opacity:0.75;max-width:420px;">
                {explanation}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Sidebar with assumptions + pipeline status ────────────────────────────────

def build_sidebar() -> tuple:
    """Return (status_slots dict, assumptions dict)."""
    with st.sidebar:
        st.header("⚙️ Underwriting Assumptions")
        ltv_pct  = st.slider("LTV (%)",              50, 80,  70)
        rate_pct = st.slider("Interest Rate (%)", 3.0, 9.0, 6.5, step=0.1)
        am_years = st.selectbox("Amortization (years)", [20, 25, 30], index=2)
        hold_yrs = st.selectbox("Hold Period (years)",  [3, 5, 7, 10], index=1)

        assumptions = {
            "ltv":               ltv_pct / 100,
            "rate":              rate_pct / 100,
            "amortization_years": am_years,
            "hold_period_years":  hold_yrs,
        }

        st.divider()
        st.header("🔄 Pipeline Status")
        slots = {}
        for name in AGENT_NAMES:
            slots[name] = st.empty()
            slots[name].write(f"⏳ {name}")
        st.divider()
        st.caption("Upload a PDF to begin.")

    return slots, assumptions


def set_status(slots: dict, name: str, state: str) -> None:
    icons = {"success": "✅", "error": "❌", "running": "⏳"}
    slots[name].write(f"{icons.get(state, '⏳')} {name}")


# ── Pipeline caching ─────────────────────────────────────────────────────────

def _file_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _run_pipeline(file_bytes: bytes, api_key: str, slots: dict) -> dict:
    """Run all 6 agents sequentially. Uses default assumptions for agents 4-6."""
    results = {}

    set_status(slots, "1. Parser", "running")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        parsed = parse_pdf(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if parsed["error"]:
        set_status(slots, "1. Parser", "error")
        results["parse_error"] = parsed["error"]
        return results
    set_status(slots, "1. Parser", "success")
    results["parsed"] = parsed

    set_status(slots, "2. Extractor", "running")
    extracted = extract_financials(parsed, api_key=api_key or None)
    if "extraction_error" in extracted:
        set_status(slots, "2. Extractor", "error")
    else:
        set_status(slots, "2. Extractor", "success")
    results["extracted"] = extracted

    if "extraction_error" in extracted:
        return results

    set_status(slots, "3. Underwriter", "running")
    uw = underwrite(extracted)
    if uw.get("underwriter_error"):
        set_status(slots, "3. Underwriter", "error")
    else:
        set_status(slots, "3. Underwriter", "success")
    results["underwriter"] = uw

    set_status(slots, "4. Risk Flagger", "running")
    risk = flag_risks(extracted, uw, api_key=api_key or None)
    if risk.get("flagger_error"):
        set_status(slots, "4. Risk Flagger", "error")
    else:
        set_status(slots, "4. Risk Flagger", "success")
    results["risk"] = risk

    set_status(slots, "5. Market Research", "running")
    market = research_market(extracted, api_key=api_key or None)
    if market.get("researcher_error"):
        set_status(slots, "5. Market Research", "error")
    else:
        set_status(slots, "5. Market Research", "success")
    results["market"] = market

    set_status(slots, "6. Report Writer", "running")
    report = write_report(
        {"extractor": extracted, "underwriter": uw, "risk_flagger": risk, "market_researcher": market},
        api_key=api_key or None,
    )
    if report.get("writer_error"):
        set_status(slots, "6. Report Writer", "error")
    else:
        set_status(slots, "6. Report Writer", "success")
    results["report"] = report

    return results


# ── History helpers ──────────────────────────────────────────────────────────

def _extract_go_no_go(memo_markdown: str) -> str:
    m = re.search(r"\*\*(NO-GO|CONDITIONAL GO|GO)\*\*", memo_markdown or "")
    if not m:
        return "Unknown"
    return {"NO-GO": "No-Go", "CONDITIONAL GO": "Conditional Go", "GO": "Go"}.get(m.group(1), m.group(1))


def _append_to_history(results: dict, uw_live: dict, source_file: str) -> None:
    extracted = results.get("extracted", {})
    report    = results.get("report", {})

    def _get(field):
        e = extracted.get(field)
        return e.get("value") if isinstance(e, dict) else None

    metrics = (uw_live or {}).get("metrics", {})
    ds      = (uw_live or {}).get("deal_score", {})

    entry = {
        "timestamp":        datetime.now(timezone.utc).isoformat(),
        "property_name":    _get("property_name") or "Unknown",
        "market":           _get("location") or "Unknown",
        "dscr":             metrics.get("dscr", {}).get("value"),
        "cap_rate_inplace": metrics.get("cap_rate_inplace", {}).get("value"),
        "deal_score":       ds.get("score"),
        "score_label":      ds.get("label"),
        "go_no_go":         _extract_go_no_go(report.get("memo_markdown", "")),
        "source_file":      source_file,
    }
    append_history_entry(entry)


# ── History tab ──────────────────────────────────────────────────────────────

def _render_history_tab() -> None:
    st.markdown("### 📚 Deal History")
    st.caption("Deals are logged automatically after a successful full pipeline run.")

    entries = load_history(n=20)

    if not entries:
        st.info("No deals analyzed yet. Screen a deal in the '📄 Screen Deal' tab to start.")
        return

    filter_col, _ = st.columns([1, 3])
    verdict_filter = filter_col.selectbox(
        "Filter by verdict", ["All", "Go", "No-Go", "Conditional Go", "Unknown"]
    )

    if verdict_filter != "All":
        entries = [e for e in entries if e.get("go_no_go", "") == verdict_filter]

    if not entries:
        st.info(f"No deals with verdict '{verdict_filter}'.")
        return

    VERDICT_BG = {
        "Go":             "#d4edda",
        "No-Go":          "#f8d7da",
        "Conditional Go": "#fff3cd",
    }

    rows = []
    for e in entries:
        rows.append({
            "Date":      e.get("timestamp", "")[:10],
            "Property":  e.get("property_name", "—"),
            "Market":    e.get("market", "—"),
            "DSCR":      f"{e['dscr']:.2f}x"          if e.get("dscr")             is not None else "—",
            "Cap Rate":  f"{e['cap_rate_inplace']:.2f}%" if e.get("cap_rate_inplace") is not None else "—",
            "Score":     f"{e['deal_score']:.0f}"       if e.get("deal_score")       is not None else "—",
            "Label":     e.get("score_label", "—"),
            "Verdict":   e.get("go_no_go", "—"),
            "Source":    e.get("source_file", "—"),
        })

    df = pd.DataFrame(rows)

    def verdict_row_style(row):
        bg = VERDICT_BG.get(row["Verdict"], "")
        return [f"background-color: {bg}" if bg else ""] * len(row)

    st.dataframe(
        df.style.apply(verdict_row_style, axis=1),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Showing last {len(entries)} deals — most recent first.")


# ── Comparison pipeline ───────────────────────────────────────────────────────

COMPARE_METRICS = [
    ("Property Name",       "extracted",   "property_name",     None),
    ("Location",            "extracted",   "location",          None),
    ("Asset Class",         "extracted",   "asset_class",       None),
    ("Units / SF",          "extracted",   "units",             None),
    ("Asking Price",        "extracted",   "asking_price",      False),
    ("Year Built",          "extracted",   "year_built",        None),
    ("Occupancy %",         "extracted",   "occupancy_pct",     True),
    ("NOI (T-12)",          "extracted",   "noi_t12",           True),
    ("Asking Cap Rate",     "extracted",   "asking_cap_rate",   True),
    ("Cap Rate (T-12)",     "underwriter", "cap_rate_inplace",  True),
    ("Cap Rate (Proforma)", "underwriter", "cap_rate_proforma", True),
    ("DSCR",                "underwriter", "dscr",              True),
    ("Debt Yield",          "underwriter", "debt_yield",        True),
    ("Cash-on-Cash",        "underwriter", "cash_on_cash",      True),
]


def _run_comparison_pipeline(file_bytes: bytes, filename: str, api_key: str) -> dict:
    result = {"filename": filename, "error": None, "extracted": None, "underwriter": None}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        parsed = parse_pdf(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if parsed["error"]:
        result["error"] = parsed["error"]
        return result

    extracted = extract_financials(parsed, api_key=api_key or None)
    if "extraction_error" in extracted:
        result["error"] = extracted["extraction_error"]
        return result

    result["extracted"]   = extracted
    result["underwriter"] = underwrite(extracted)
    return result


def _get_compare_value(result: dict, source: str, key: str):
    if result.get("error"):
        return None
    if source == "extracted":
        entry = result.get("extracted", {}).get(key)
        return entry.get("value") if isinstance(entry, dict) else None
    if source == "underwriter":
        return result.get("underwriter", {}).get("metrics", {}).get(key, {}).get("value")
    return None


def _fmt_compare(key: str, value) -> str:
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


def _compute_winner(results: list) -> int:
    scores = []
    for r in results:
        dscr = _get_compare_value(r, "underwriter", "dscr") or 0.0
        cap  = _get_compare_value(r, "underwriter", "cap_rate_inplace") or 0.0
        scores.append(
            max(0.0, (dscr - 0.8) / (2.0 - 0.8)) +
            max(0.0, (cap  - 3.0) / (10.0 - 3.0))
        )
    return -1 if all(s == 0.0 for s in scores) else scores.index(max(scores))


def _render_comparison_tab(api_key: str) -> None:
    st.markdown("### ⚖️ Compare up to 3 Deals Side-by-Side")
    st.caption(
        "Runs Parser → Extractor → Underwriter on each file. "
        "Market Research and Report Writer are skipped for speed."
    )

    uploaded_files = st.file_uploader(
        "Upload 2–3 Offering Memoranda (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        key="compare_uploader",
    )

    if not uploaded_files:
        st.info("Upload 2–3 PDFs above to begin the comparison.")
        return

    if len(uploaded_files) > 3:
        st.warning("Maximum 3 files supported — using the first 3.")
        uploaded_files = uploaded_files[:3]

    if len(uploaded_files) < 2:
        st.info("Add at least one more PDF to enable comparison.")
        return

    file_data   = [(f.name, f.read()) for f in uploaded_files]
    file_hashes = sorted([_file_hash(b) for _, b in file_data])

    if (
        st.session_state.get("comp_hashes") == file_hashes
        and "comp_results" in st.session_state
    ):
        deal_results = st.session_state["comp_results"]
    else:
        deal_results = []
        total = len(file_data)
        bar   = st.progress(0, text="Starting comparison pipeline…")
        for i, (fname, fbytes) in enumerate(file_data):
            bar.progress(i / total, text=f"Processing {fname}…")
            deal_results.append(_run_comparison_pipeline(fbytes, fname, api_key))
        bar.progress(1.0, text="Done.")
        st.session_state["comp_results"] = deal_results
        st.session_state["comp_hashes"]  = file_hashes

    winner_idx = _compute_winner(deal_results)

    st.markdown("---")
    header_cols = st.columns(len(deal_results))
    for i, (col, r) in enumerate(zip(header_cols, deal_results)):
        badge = "  🏆 **Winner**" if i == winner_idx else ""
        prop  = _get_compare_value(r, "extracted", "property_name") or r["filename"]
        if r.get("error"):
            col.error(f"❌ **{r['filename']}**\n\n{r['error']}")
        else:
            col.success(f"**{prop}**{badge}")
            col.caption(r["filename"])

    col_names    = [
        _get_compare_value(r, "extracted", "property_name") or r["filename"]
        for r in deal_results
    ]
    display_data = {}
    numeric_data = {}
    higher_map   = {}

    for label, source, key, higher in COMPARE_METRICS:
        disp_vals, num_vals = [], []
        for r in deal_results:
            raw = _get_compare_value(r, source, key)
            disp_vals.append(_fmt_compare(key, raw))
            num_vals.append(raw if isinstance(raw, (int, float)) else None)
        display_data[label] = disp_vals
        numeric_data[label] = num_vals
        higher_map[label]   = higher

    df_disp = pd.DataFrame(display_data, index=col_names).T
    df_disp.index.name = "Metric"

    n_rows, n_cols = df_disp.shape
    styles = [[""] * n_cols for _ in range(n_rows)]
    for row_i, label in enumerate(df_disp.index):
        higher = higher_map.get(label)
        if higher is None:
            continue
        nums  = numeric_data[label]
        valid = [(ci, v) for ci, v in enumerate(nums) if v is not None]
        if len(valid) < 2:
            continue
        best_i  = (max if higher else min)(valid, key=lambda x: x[1])[0]
        worst_i = (min if higher else max)(valid, key=lambda x: x[1])[0]
        styles[row_i][best_i]  = "background-color: #d4edda; font-weight: bold"
        styles[row_i][worst_i] = "background-color: #f8d7da"

    styles_df = pd.DataFrame(styles, index=df_disp.index, columns=df_disp.columns)
    st.dataframe(df_disp.style.apply(lambda _: styles_df, axis=None), use_container_width=True)
    st.caption(
        "🟢 **Bold** = best value per row · 🔴 = worst value per row · "
        "🏆 Winner = highest combined DSCR + Cap Rate score (normalized)"
    )


# ── Single-deal tab ──────────────────────────────────────────────────────────

def _render_single_deal_tab(api_key: str, slots: dict, assumptions: dict) -> None:
    st.divider()

    uploaded_file = st.file_uploader(
        "Upload an Offering Memorandum (PDF)",
        type=["pdf"],
        help="Upload a CRE deal OM to extract and underwrite automatically.",
    )

    if uploaded_file is None:
        return

    st.success(f"Uploaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

    file_bytes = uploaded_file.read()
    file_hash  = _file_hash(file_bytes)

    if (
        st.session_state.get("file_hash") == file_hash
        and "results" in st.session_state
    ):
        results = st.session_state["results"]
        for name in AGENT_NAMES:
            slots[name].write(f"✅ {name}")
        if results.get("report", {}).get("writer_error"):
            slots["6. Report Writer"].write("❌ 6. Report Writer")
    else:
        with st.spinner("Running 6-agent pipeline…"):
            results = _run_pipeline(file_bytes, api_key, slots)
        st.session_state["results"]   = results
        st.session_state["file_hash"] = file_hash
        st.session_state.pop("history_appended_for", None)

    if results.get("parse_error"):
        st.error(f"PDF parse failed: {results['parse_error']}")
        return

    # Live underwriter recompute with current sidebar assumptions (instant, no API)
    extracted = results.get("extracted")
    uw_live   = underwrite(extracted, assumptions=assumptions) if extracted else None

    # ── Deal Score card (top of page) ────────────────────────────────────────
    if uw_live and not uw_live.get("underwriter_error"):
        render_deal_score(uw_live.get("deal_score", {}))

    # ── Raw text expander ────────────────────────────────────────────────────
    parsed = results.get("parsed", {})
    with st.expander("View raw extracted text"):
        st.text_area(
            "Document text (first 3,000 chars)",
            value=parsed.get("full_text", "")[:3000],
            height=200,
            disabled=True,
        )

    # ── Section 1: Extracted data ────────────────────────────────────────────
    if extracted:
        st.subheader("1 · Extracted Financial Data")
        render_extraction(extracted)

    # ── Section 2: Underwriter (live — reflects sidebar assumptions) ─────────
    if uw_live:
        st.subheader("2 · Financial Metrics")
        render_underwriter(uw_live)

    # ── Section 3: Risk flags (from pipeline run with default assumptions) ────
    risk = results.get("risk")
    if risk:
        st.subheader("3 · Risk Assessment")
        render_risk_flags(risk)

    # ── Section 4: Market context ─────────────────────────────────────────────
    market = results.get("market")
    if market:
        st.subheader("4 · Market Context")
        render_market_research(market)

    # ── Section 5: IC Memo + exports ─────────────────────────────────────────
    report = results.get("report")
    if report:
        if report.get("writer_error"):
            st.error(f"Report writer error: {report['writer_error']}")
        else:
            st.divider()
            st.subheader("5 · Investment Committee Memo")
            memo_md = report["memo_markdown"]
            st.markdown(memo_md)
            st.divider()

            # Append to history once per file (not on every Streamlit rerun)
            if st.session_state.get("history_appended_for") != file_hash:
                _append_to_history(results, uw_live, uploaded_file.name)
                st.session_state["history_appended_for"] = file_hash

            property_name = report.get("property_name", "Deal")
            safe_name     = property_name.replace(" ", "_")

            dl_col1, dl_col2 = st.columns(2)

            with dl_col1:
                try:
                    pdf_bytes = generate_pdf_bytes(memo_md)
                    dl_col1.download_button(
                        label="⬇️ Download IC Memo (PDF)",
                        data=pdf_bytes,
                        file_name=f"IC_Memo_{safe_name}.pdf",
                        mime="application/pdf",
                        type="primary",
                    )
                except Exception as e:
                    dl_col1.warning(f"PDF export unavailable: {e}")

            with dl_col2:
                if uw_live and risk:
                    try:
                        xlsx_bytes = export_excel_model(
                            extracted or {},
                            uw_live,
                            risk,
                            property_name=property_name,
                        )
                        dl_col2.download_button(
                            label="📊 Download Excel Model",
                            data=xlsx_bytes,
                            file_name=f"Model_{safe_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    except Exception as e:
                        dl_col2.warning(f"Excel export unavailable: {e}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    st.title("🏢 AI Deal Screening Agent")
    st.caption("Project Destined Hackathon · June 2026")

    # Local dev: loaded from .env via load_dotenv() above.
    # Streamlit Cloud: set ANTHROPIC_API_KEY in the app's Secrets panel.
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error(
            "ANTHROPIC_API_KEY not found. "
            "**Local:** add it to `.env`. "
            "**Cloud:** add it in the Streamlit app Secrets panel."
        )

    slots, assumptions = build_sidebar()

    tab1, tab2, tab3 = st.tabs(["📄 Screen Deal", "⚖️ Compare Deals", "📚 Deal History"])

    with tab1:
        _render_single_deal_tab(api_key, slots, assumptions)

    with tab2:
        _render_comparison_tab(api_key)

    with tab3:
        _render_history_tab()


if __name__ == "__main__":
    main()
