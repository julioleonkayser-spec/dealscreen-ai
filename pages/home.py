"""Home page — hero, value proposition, and how it works."""

import streamlit as st

from utils.components import inject_css

inject_css()

# ── Hero ─────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="ds-hero">
      <div class="ds-product-badge">⚡ AI-Powered · 6-Agent Pipeline</div>
      <div class="ds-hero-title">
        <span class="ds-hero-accent">DealScreen AI</span><br>
        CRE Deal Screening Agent
      </div>
      <div class="ds-hero-sub">
        Upload an Offering Memorandum and get a full underwriting analysis,
        risk assessment, and Investment Committee memo in seconds — not hours.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_l, col_btn, col_r = st.columns([2, 1.4, 2])
with col_btn:
    if st.button(
        "Open an Offering Memorandum",
        type="primary",
        use_container_width=True,
    ):
        st.switch_page("pages/screen_deal.py")

st.markdown(
    '<hr style="border:none;border-top:1px solid #E8EDF5;margin:32px 0 32px;">',
    unsafe_allow_html=True,
)

# ── How it works ─────────────────────────────────────────────────────────────

st.markdown(
    """
    <div style="text-align:center;margin-bottom:4px;">
      <span style="font-size:11px;font-weight:700;text-transform:uppercase;
                   letter-spacing:.09em;color:#94A3B8;">How It Works</span>
    </div>
    <div style="text-align:center;font-size:20px;font-weight:800;
                color:#0F1B38;letter-spacing:-.02em;margin-bottom:4px;">
      From PDF to IC Memo in three steps
    </div>
    <div style="text-align:center;font-size:13px;color:#64748B;margin-bottom:0;">
      A six-agent pipeline handles extraction, underwriting, risk flagging,
      market research, and report generation automatically.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ds-steps">

      <div class="ds-step-card">
        <div class="ds-step-num">1</div>
        <div class="ds-step-title">Upload the OM</div>
        <div class="ds-step-desc">
          Drop in any CRE Offering Memorandum PDF. The parser extracts
          page-by-page text and feeds it to the AI extractor.
        </div>
      </div>

      <div class="ds-step-card">
        <div class="ds-step-num">2</div>
        <div class="ds-step-title">AI Pipeline Runs</div>
        <div class="ds-step-desc">
          Six specialized agents — Extractor, Underwriter, Risk Flagger,
          Market Researcher, and Report Writer — analyze the deal in sequence.
        </div>
      </div>

      <div class="ds-step-card">
        <div class="ds-step-num">3</div>
        <div class="ds-step-title">IC Memo &amp; Decision</div>
        <div class="ds-step-desc">
          Receive a full Investment Committee memo with key metrics, risk flags,
          market context, and a GO / NO-GO / CONDITIONAL GO verdict.
        </div>
      </div>

    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div style="height:36px;"></div>', unsafe_allow_html=True)

# ── Stats strip ───────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        '<div style="text-align:center;">'
        '<div style="font-size:28px;font-weight:900;color:#1B3A6B;">6</div>'
        '<div style="font-size:12px;color:#64748B;margin-top:2px;">Specialized AI Agents</div>'
        "</div>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        '<div style="text-align:center;">'
        '<div style="font-size:28px;font-weight:900;color:#1B3A6B;">5</div>'
        '<div style="font-size:12px;color:#64748B;margin-top:2px;">Key Underwriting Metrics</div>'
        "</div>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        '<div style="text-align:center;">'
        '<div style="font-size:28px;font-weight:900;color:#1B3A6B;">7</div>'
        '<div style="font-size:12px;color:#64748B;margin-top:2px;">Risk Flag Checks</div>'
        "</div>",
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        '<div style="text-align:center;">'
        '<div style="font-size:28px;font-weight:900;color:#1B3A6B;">&lt;60s</div>'
        '<div style="font-size:12px;color:#64748B;margin-top:2px;">Typical Analysis Time</div>'
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
st.caption(
    "_DealScreen AI is a decision-support tool, not investment advice. "
    "All output should be verified against primary source documents and qualified advisors._"
)
