"""Screen Deal page — single OM upload, 6-agent pipeline, results."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.underwriter import underwrite
from utils.components import (
    PIPELINE_STAGES,
    empty_state,
    inject_css,
    page_header,
    render_deal_score_card,
    render_extraction,
    render_kpi_row,
    render_market_research,
    render_pipeline_bar,
    render_risk_flags,
    render_underwriter,
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

# ── Upload ────────────────────────────────────────────────────────────────────

uploaded_file = st.file_uploader(
    "Offering Memorandum (PDF)",
    type=["pdf"],
    help="Accepts any text-extractable CRE PDF. Scanned image-only PDFs will yield limited data.",
    label_visibility="collapsed",
)

if uploaded_file is None:
    empty_state(
        "📄",
        "No document uploaded",
        "Upload a PDF Offering Memorandum above to begin the analysis. "
        "The pipeline extracts financials, underwrites the deal, and drafts an IC memo automatically.",
    )
    st.stop()

file_bytes = uploaded_file.read()
fhash      = file_hash(file_bytes)
cached     = st.session_state.get("file_hash") == fhash and "results" in st.session_state

st.markdown(
    f'<div style="font-size:13px;color:#64748B;padding:6px 0 4px;">'
    f'<strong style="color:#0F1B38;">{uploaded_file.name}</strong>'
    f'&ensp;·&ensp;{uploaded_file.size / 1024:.1f} KB</div>',
    unsafe_allow_html=True,
)

# ── Run pipeline or restore from cache ───────────────────────────────────────

# Determine final state for each stage after the pipeline finishes
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
        # Stages that never ran remain absent → rendered as idle
else:
    stage_states: dict = {}
    bar_slot = st.empty()

    def on_step(stage: str, msg: str) -> None:
        stage_states[stage] = "running"
        with bar_slot:
            render_pipeline_bar(stage_states)

    with st.status("Analyzing deal…", expanded=True) as status_box:
        results = run_pipeline(file_bytes, api_key, on_step=on_step)

        # Finalise each stage that was visited
        for stage in PIPELINE_STAGES:
            if stage not in stage_states:
                break  # Pipeline stopped here; remaining stages never ran
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

# ── Deal score + KPI row ──────────────────────────────────────────────────────

if uw_live and not uw_live.get("underwriter_error"):
    render_deal_score_card(uw_live.get("deal_score", {}))
    render_kpi_row(uw_live, extracted)

# ── Tabbed results ────────────────────────────────────────────────────────────

tab_overview, tab_financials, tab_risks, tab_market, tab_memo = st.tabs(
    ["📋 Overview", "📊 Financials", "⚠️ Risks", "🌐 Market", "📝 IC Memo"]
)

with tab_overview:
    st.markdown("#### Extracted Financial Data")
    if extracted:
        render_extraction(extracted)
    parsed = results.get("parsed", {})
    with st.expander("View source document text"):
        st.text_area(
            "First 3,000 characters extracted from the PDF",
            value=parsed.get("full_text", "")[:3000],
            height=200,
            disabled=True,
        )

with tab_financials:
    st.markdown("#### Financial Metrics")
    if uw_live and uw_live.get("underwriter_error"):
        st.error(
            f"**Underwriting could not be completed.** {uw_live['underwriter_error']}\n\n"
            "Check the Overview tab for missing data fields."
        )
    elif uw_live:
        render_underwriter(uw_live)
    else:
        st.info("Underwriting metrics are unavailable — the extraction step did not complete.")

with tab_risks:
    st.markdown("#### Risk Assessment")
    risk = results.get("risk")
    if risk:
        render_risk_flags(risk)
    elif results.get("extracted", {}).get("extraction_error"):
        st.warning("Risk assessment could not run because financial extraction failed.")
    else:
        st.info("Risk assessment not yet available.")

with tab_market:
    st.markdown("#### Market Context")
    market = results.get("market")
    if market:
        render_market_research(market)
    else:
        st.info("Market research not yet available.")

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

        # st.markdown renders GFM natively — do not wrap in an HTML block
        # (CommonMark treats <div> as a raw block, which suppresses markdown rendering)
        st.markdown(memo_md)

        # Append to history once per file — not on every rerun
        if st.session_state.get("history_appended_for") != fhash:
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
                "source_file":      uploaded_file.name,
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
