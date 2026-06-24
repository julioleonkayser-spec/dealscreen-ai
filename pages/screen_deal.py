"""Screen Deal page — single OM upload, 6-agent pipeline, results."""

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.underwriter import underwrite
from examples.sample_deals import SAMPLE_DEALS, SAMPLE_NAMES
from utils.components import (
    PIPELINE_STAGES,
    empty_state,
    inject_css,
    page_header,
    render_deal_score_card,
    render_extraction,
    render_ic_summary_strip,
    render_irr_multiple_kpi,
    render_kpi_row,
    render_market_research,
    render_pipeline_bar,
    render_risk_flags,
    render_sensitivity_table,
    render_stress_test,
    render_underwriter,
    source_tag,
)
from utils.formatters import extract_go_no_go
from utils.history import append_history_entry
from utils.pipeline import file_hash, run_pipeline
from utils.pdf_export import generate_pdf_bytes
from utils.excel_export import export_excel_model

inject_css()

# ── API key ───────────────────────────────────────────────────────────────────

api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.caption("UNDERWRITING ASSUMPTIONS")
    ltv_pct  = st.slider("LTV (%)",           50, 80, 70)
    rate_pct = st.slider("Interest Rate (%)", 3.0, 9.0, 6.5, step=0.1)
    am_years = st.selectbox("Amortization (years)", [20, 25, 30], index=2)
    hold_yrs = st.selectbox("Hold Period (years)",  [3, 5, 7, 10], index=1)

    assumptions = {
        "ltv":                ltv_pct  / 100,
        "rate":               rate_pct / 100,
        "amortization_years": am_years,
        "hold_period_years":  hold_yrs,
    }

    if not api_key:
        st.divider()
        st.error(
            "**API key not configured.**\n\n"
            "Local: add `ANTHROPIC_API_KEY` to `.env`.\n\n"
            "Cloud: add it in the app's Secrets panel."
        )

# ── Page header ───────────────────────────────────────────────────────────────

page_header(
    "Screen a Deal",
    "Upload an Offering Memorandum to run the six-agent AI underwriting pipeline.",
)

# ── Feature 3: Example Deals Library ─────────────────────────────────────────

_ex_options = ["— Select —"] + SAMPLE_NAMES
_ex_label   = st.selectbox("Load an example deal", _ex_options, key="example_select")

if _ex_label != "— Select —":
    _ex_idx = SAMPLE_NAMES.index(_ex_label)
    _ex_key = f"__example_{_ex_idx}"
    if st.session_state.get("file_hash") != _ex_key:
        st.session_state["results"]   = SAMPLE_DEALS[_ex_idx]
        st.session_state["file_hash"] = _ex_key
        st.session_state.pop("history_appended_for", None)
else:
    # Clear example mode when user returns to "— Select —"
    if st.session_state.get("file_hash", "").startswith("__example_"):
        st.session_state.pop("file_hash", None)
        st.session_state.pop("results", None)

# ── Upload ────────────────────────────────────────────────────────────────────

uploaded_file = st.file_uploader(
    "Offering Memorandum (PDF)",
    type=["pdf"],
    help="Accepts any text-extractable CRE PDF. Scanned image-only PDFs will yield limited data.",
    label_visibility="collapsed",
)

_in_example = st.session_state.get("file_hash", "").startswith("__example_")

if uploaded_file is None and not _in_example:
    empty_state(
        "📄",
        "No document uploaded",
        "Upload a PDF Offering Memorandum above to begin the analysis. "
        "The pipeline extracts financials, underwrites the deal, and drafts an IC memo automatically.",
    )
    st.stop()

# Resolve source name and file hash before the pipeline section
if _in_example and uploaded_file is None:
    fhash        = st.session_state["file_hash"]
    cached       = True
    _source_name = _ex_label
    st.info("⚠️ This is a sample deal for demonstration purposes only.")
else:
    file_bytes   = uploaded_file.read()
    fhash        = file_hash(file_bytes)
    cached       = st.session_state.get("file_hash") == fhash and "results" in st.session_state
    _source_name = uploaded_file.name
    st.markdown(
        f'<div style="font-size:13px;color:#64748B;padding:6px 0 4px;">'
        f'<strong style="color:#0F1B38;">{uploaded_file.name}</strong>'
        f'&ensp;·&ensp;{uploaded_file.size / 1024:.1f} KB</div>',
        unsafe_allow_html=True,
    )

# ── Run pipeline or restore from cache ───────────────────────────────────────

_STAGE_OK = {
    "Parser":          lambda r: not r.get("parse_error"),
    "Extractor":       lambda r: not r.get("extracted", {}).get("extraction_error"),
    "Underwriter":     lambda r: not r.get("underwriter", {}).get("underwriter_error"),
    "Risk Flagger":    lambda r: not r.get("risk", {}).get("flagger_error"),
    "Market Research": lambda r: not r.get("market", {}).get("researcher_error"),
    "Report Writer":   lambda r: not r.get("report", {}).get("writer_error"),
}

if cached:
    results      = st.session_state["results"]
    stage_states = {}
    for stage in PIPELINE_STAGES:
        check = _STAGE_OK.get(stage)
        if check and check(results):
            stage_states[stage] = "success"
        elif stage in [k for k in results if k != "parse_error"]:
            stage_states[stage] = "error"
else:
    stage_states: dict = {}
    bar_slot = st.empty()

    def on_step(stage: str, msg: str) -> None:
        stage_states[stage] = "running"
        with bar_slot:
            render_pipeline_bar(stage_states)

    with st.status("Analyzing deal…", expanded=True) as status_box:
        _t0 = time.time()
        results = run_pipeline(file_bytes, api_key, on_step=on_step)
        st.session_state["_last_pipeline_duration"] = round(time.time() - _t0, 1)

        for stage in PIPELINE_STAGES:
            if stage not in stage_states:
                break
            check = _STAGE_OK.get(stage)
            stage_states[stage] = "success" if (check and check(results)) else "error"

        ok    = not results.get("parse_error")
        label = "Analysis complete." if ok else "Pipeline stopped — see error below."
        status_box.update(label=label, state="complete" if ok else "error", expanded=False)

    st.session_state["results"]   = results
    st.session_state["file_hash"] = fhash
    st.session_state.pop("history_appended_for", None)

render_pipeline_bar(stage_states)

# ── Guard on parse failure ────────────────────────────────────────────────────

if results.get("parse_error"):
    st.error(
        f"**PDF could not be parsed.** {results['parse_error']}\n\n"
        "Ensure the file is a text-extractable PDF, not a scanned image."
    )
    st.stop()

# ── Live underwriter recompute with current sidebar assumptions ───────────────

extracted = results.get("extracted")
uw_live   = underwrite(extracted, assumptions=assumptions) if extracted else None

# ── Run history tracking ──────────────────────────────────────────────────────

if not cached:
    if "run_history" not in st.session_state:
        st.session_state["run_history"] = []
    def _fld(field):
        e = (extracted or {}).get(field, {})
        return e.get("value") if isinstance(e, dict) else None
    _missing_critical = not _fld("asking_price") or not _fld("noi_t12")
    st.session_state["run_history"].append({
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "deal_name":  _fld("property_name") or _source_name,
        "score":      (uw_live or {}).get("deal_score", {}).get("score"),
        "status":     "missing_critical" if _missing_critical else "complete",
        "duration_s": st.session_state.pop("_last_pipeline_duration", None),
    })

# ── IC Summary Strip + Deal score + KPI row ──────────────────────────────────

if uw_live and not uw_live.get("underwriter_error"):
    render_ic_summary_strip(uw_live, results.get("risk"), results.get("report"))
    render_deal_score_card(uw_live.get("deal_score", {}))
    render_kpi_row(uw_live, extracted)

    # Feature 3: IRR & Equity Multiple KPI cards
    if extracted:
        def _fv(field):
            e = extracted.get(field, {})
            return e.get("value") if isinstance(e, dict) else None
        _price = _fv("asking_price")
        _noi   = _fv("noi_proforma") or _fv("noi_t12")
        _cap   = _fv("asking_cap_rate")           # in % (e.g. 5.25)
        _hold  = assumptions.get("hold_period_years", 5)
        if _price and _noi:
            _exit_cap = (_cap / 100) if _cap else (_noi / _price)
            render_irr_multiple_kpi(_price, _noi, _exit_cap, _hold)

# ── Tabbed results ────────────────────────────────────────────────────────────

tab_overview, tab_financials, tab_risks, tab_market, tab_memo, tab_comps = st.tabs([
    "📋 Overview", "📊 Financials", "⚠️ Risks", "🌐 Market", "📝 IC Memo", "🏙️ Market Data & Comps",
])

# ── Tab: Overview ─────────────────────────────────────────────────────────────

with tab_overview:
    st.markdown("#### Extracted Financial Data")
    if extracted:
        render_extraction(extracted)

        # Feature 2: source tags for key metrics
        _key_refs = [
            ("gross_potential_rent", "GPR"),
            ("occupancy_pct",        "Occupancy"),
            ("noi_t12",              "T-12 NOI"),
            ("asking_cap_rate",      "Cap Rate"),
            ("units",                "Units"),
            ("asking_price",         "Asking Price"),
        ]
        _ref_parts = []
        for _field, _name in _key_refs:
            _entry = extracted.get(_field, {})
            if isinstance(_entry, dict) and _entry.get("source_page"):
                _ref_parts.append(f"**{_name}** p.{_entry['source_page']}")
        if _ref_parts:
            source_tag("OM page references — " + " · ".join(_ref_parts))

    parsed = results.get("parsed", {})
    with st.expander("View source document text"):
        st.text_area(
            "First 3,000 characters extracted from the PDF",
            value=parsed.get("full_text", "")[:3000],
            height=200,
            disabled=True,
        )

# ── Tab: Financials ───────────────────────────────────────────────────────────

with tab_financials:
    st.markdown("#### Financial Metrics")
    if uw_live and uw_live.get("underwriter_error"):
        st.error(
            f"**Underwriting could not be completed.** {uw_live['underwriter_error']}\n\n"
            "Check the Overview tab for missing data fields."
        )
    elif uw_live:
        render_underwriter(uw_live)

        # Feature 2: source tags for financial inputs
        if extracted:
            _fin_refs = [
                ("noi_t12",        "T-12 NOI"),
                ("noi_proforma",   "Proforma NOI"),
                ("asking_cap_rate","Cap Rate"),
                ("asking_price",   "Asking Price"),
            ]
            _fin_parts = []
            for _field, _name in _fin_refs:
                _entry = extracted.get(_field, {})
                if isinstance(_entry, dict) and _entry.get("source_page"):
                    _fin_parts.append(f"**{_name}** p.{_entry['source_page']}")
            if _fin_parts:
                source_tag("OM page references — " + " · ".join(_fin_parts))

        # Feature 2: market cap rate benchmark comparison
        _market_avg_cap = st.session_state.get("market_avg_cap_rate")
        _deal_cap       = uw_live.get("metrics", {}).get("cap_rate_inplace", {}).get("value")
        if _deal_cap is not None:
            if _market_avg_cap is not None:
                _diff = _deal_cap - _market_avg_cap
                if _diff > 0:
                    _tag_color, _tag_bg, _verdict = "#16A34A", "#DCFCE7", "Above market yield"
                else:
                    _tag_color, _tag_bg, _verdict = "#B45309", "#FEF3C7", "Below market yield"
                st.markdown(
                    f'<div style="font-size:13px;color:#475569;margin:6px 0 12px;">'
                    f'Deal cap rate: <strong>{_deal_cap:.2f}%</strong> vs '
                    f'market average: <strong>{_market_avg_cap:.2f}%</strong>'
                    f'&ensp;<span style="font-size:11px;font-weight:700;padding:2px 8px;'
                    f'border-radius:12px;background:{_tag_bg};color:{_tag_color};">'
                    f'{_verdict}</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption(
                    "Market benchmark: N/A — upload a comps CSV in the Market Data & Comps tab."
                )
    else:
        st.info("Underwriting metrics are unavailable — the extraction step did not complete.")
    render_sensitivity_table(extracted, assumptions)
    render_stress_test(extracted, assumptions)

# ── Tab: Risks ────────────────────────────────────────────────────────────────

with tab_risks:
    st.markdown("#### Risk Assessment")
    risk = results.get("risk")
    if risk:
        render_risk_flags(risk)
    elif results.get("extracted", {}).get("extraction_error"):
        st.warning("Risk assessment could not run because financial extraction failed.")
    else:
        st.info("Risk assessment not yet available.")

# ── Tab: Market ───────────────────────────────────────────────────────────────

with tab_market:
    st.markdown("#### Market Context")
    market = results.get("market")
    if market:
        render_market_research(market)
    else:
        st.info("Market research not yet available.")

# ── Tab: IC Memo ──────────────────────────────────────────────────────────────

with tab_memo:
    report = results.get("report")
    if not report:
        st.info("The IC Memo will appear here once the full pipeline completes.")
    elif report.get("writer_error"):
        st.error(
            f"**IC Memo could not be drafted.** {report['writer_error']}\n\n"
            "The underlying data is still available in the other tabs."
        )
    else:
        memo_md = report["memo_markdown"]
        st.markdown(memo_md)

        # Append to persistent history (skip for example deals)
        if not _in_example and st.session_state.get("history_appended_for") != fhash:
            def _get(field):
                e = (extracted or {}).get(field)
                return e.get("value") if isinstance(e, dict) else None

            metrics = (uw_live or {}).get("metrics", {})
            ds      = (uw_live or {}).get("deal_score", {})
            append_history_entry({
                "timestamp":        datetime.now(timezone.utc).isoformat(),
                "property_name":    _get("property_name") or "Unknown",
                "market":           _get("location") or "Unknown",
                "dscr":             metrics.get("dscr", {}).get("value"),
                "cap_rate_inplace": metrics.get("cap_rate_inplace", {}).get("value"),
                "deal_score":       ds.get("score"),
                "score_label":      ds.get("label"),
                "go_no_go":         extract_go_no_go(memo_md),
                "source_file":      _source_name,
            })
            st.session_state["history_appended_for"] = fhash

        # ── Export buttons ────────────────────────────────────────────────────
        st.divider()
        property_name = report.get("property_name", "Deal")
        safe_name     = property_name.replace(" ", "_")
        dl1, dl2      = st.columns(2)

        with dl1:
            try:
                st.download_button(
                    label="⬇️  Download IC Memo (PDF)",
                    data=generate_pdf_bytes(memo_md),
                    file_name=f"IC_Memo_{safe_name}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as exc:
                st.warning(f"PDF export unavailable: {exc}")

        with dl2:
            if uw_live and risk:
                try:
                    st.download_button(
                        label="📊  Download Excel Model",
                        data=export_excel_model(extracted or {}, uw_live, risk,
                                                property_name=property_name),
                        file_name=f"Model_{safe_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.warning(f"Excel export unavailable: {exc}")

# ── Tab: Market Data & Comps (Feature 1) ─────────────────────────────────────

with tab_comps:
    st.markdown("#### Market Data & Comps")
    st.caption(
        "Paste a listing URL and/or upload a market comps CSV export from CoStar, Crexi, or LoopNet."
    )

    col_url, col_platform = st.columns([3, 1])
    with col_url:
        listing_url = st.text_input(
            "Listing URL",
            value=st.session_state.get("comps_listing_url", ""),
            placeholder="https://www.crexi.com/properties/...",
            key="comps_listing_url_input",
        )
    with col_platform:
        platform = st.selectbox(
            "Source Platform",
            ["CoStar", "Crexi", "LoopNet", "Other"],
            key="comps_platform_select",
        )

    # Persist URL + platform in session state for deal summary access
    if listing_url:
        st.session_state["comps_listing_url"] = listing_url
    st.session_state["comps_platform"] = platform

    comps_file = st.file_uploader(
        "Upload market comps export",
        type=["csv"],
        help="Export a comps table from CoStar, Crexi, or LoopNet as CSV.",
        key="comps_csv_upload",
    )

    if comps_file is not None:
        try:
            df_comps = pd.read_csv(comps_file)
            st.markdown(f"**{len(df_comps)} comps loaded** · showing first 10 rows")
            st.dataframe(df_comps.head(10), use_container_width=True, hide_index=True)

            # ── Summary metrics (handle missing columns gracefully) ────────────

            def _avg_col(df: pd.DataFrame, candidates: list[str]) -> str:
                """Return formatted average for the first matching column, or 'N/A'."""
                for col in candidates:
                    matches = [c for c in df.columns if c.strip().lower() == col.lower()]
                    if matches:
                        series = pd.to_numeric(df[matches[0]], errors="coerce").dropna()
                        if not series.empty:
                            return f"{series.mean():.2f}"
                return "N/A"

            avg_cap  = _avg_col(df_comps, ["cap rate", "cap_rate", "caprate", "cap"])
            avg_rent = _avg_col(df_comps, ["avg rent", "avg_rent", "rent", "monthly rent", "asking rent"])
            avg_ppu  = _avg_col(df_comps, ["price/unit", "price per unit", "price_per_unit", "ppu", "$/unit"])

            # Feature 2: persist numeric market avg cap rate for Financials tab benchmark comparison
            if avg_cap != "N/A":
                st.session_state["market_avg_cap_rate"] = float(avg_cap)
            else:
                st.session_state.pop("market_avg_cap_rate", None)

            m1, m2, m3 = st.columns(3)
            m1.metric("Avg Cap Rate (%)",     avg_cap  if avg_cap  != "N/A" else "N/A")
            m2.metric("Avg Rent ($)",          avg_rent if avg_rent != "N/A" else "N/A")
            m3.metric("Avg Price / Unit ($)",  avg_ppu  if avg_ppu  != "N/A" else "N/A")

            if avg_cap == avg_rent == avg_ppu == "N/A":
                st.info(
                    "Could not compute summary metrics — column names were not recognized. "
                    "Expected columns such as: **Cap Rate**, **Avg Rent**, **Price/Unit**."
                )

            # ── Bar chart for numeric columns ─────────────────────────────────
            numeric_cols = df_comps.select_dtypes(include="number").columns.tolist()
            if numeric_cols:
                chart_col = st.selectbox(
                    "Chart column",
                    numeric_cols,
                    key="comps_chart_col",
                )
                chart_data = df_comps[chart_col].dropna().reset_index(drop=True)
                # Label by property name if available, else by index
                name_cols = [c for c in df_comps.columns if "name" in c.lower() or "property" in c.lower() or "address" in c.lower()]
                if name_cols:
                    chart_data.index = df_comps[name_cols[0]].fillna("").astype(str).values[:len(chart_data)]
                st.bar_chart(chart_data, use_container_width=True)

        except Exception as exc:
            st.error(f"Could not parse CSV: {exc}")
    else:
        st.markdown(
            """<div style="text-align:center;padding:40px 20px;
                          background:#F8FAFC;border:1px dashed #CBD5E1;
                          border-radius:10px;margin-top:12px;">
              <div style="font-size:28px;margin-bottom:12px;">📊</div>
              <div style="font-size:14px;font-weight:600;color:#0F1B38;margin-bottom:6px;">
                No comps uploaded yet
              </div>
              <div style="font-size:13px;color:#64748B;max-width:320px;margin:0 auto;">
                Export a comps table from CoStar, Crexi, or LoopNet as CSV and upload it above.
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
