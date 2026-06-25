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

# ── Architecture Diagram (Feature 4) ─────────────────────────────────────────

st.markdown(
    '<hr style="border:none;border-top:1px solid #E8EDF5;margin:32px 0 32px;">',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="text-align:center;margin-bottom:4px;">
      <span style="font-size:11px;font-weight:700;text-transform:uppercase;
                   letter-spacing:.09em;color:#94A3B8;">System Architecture</span>
    </div>
    <div style="text-align:center;font-size:20px;font-weight:800;
                color:#0F1B38;letter-spacing:-.02em;margin-bottom:4px;">
      Agent Architecture — How DealScreen AI Works
    </div>
    <div style="text-align:center;font-size:13px;color:#64748B;margin-bottom:20px;">
      Six specialized agents run in sequence. Deterministic Python handles math;
      Claude models handle language understanding and generation.
    </div>
    """,
    unsafe_allow_html=True,
)

_DOT = """
digraph DealScreenAI {
    rankdir=TB
    graph [bgcolor="#FAFBFC" pad="0.4" nodesep="0.5" ranksep="0.6"]
    node  [fontname="Arial" fontsize=11 style="filled,rounded" shape=box margin="0.2,0.1"]
    edge  [fontname="Arial" fontsize=9 color="#94A3B8"]

    OM [label="OM PDF\\n(uploaded by analyst)"
        fillcolor="#EEF4FF" color="#C7D9F8" fontcolor="#1B3A6B" shape=folder]

    Orch [label="Orchestrator\\n(utils/pipeline.py)"
          fillcolor="#1B3A6B" color="#0F1B38" fontcolor="white"]

    Parser [label="1 · Parser\\npdfplumber — text extraction"
            fillcolor="#F8FAFC" color="#CBD5E1" fontcolor="#0F1B38"]

    Extractor [label="2 · Extractor\\nClaude Haiku — field extraction"
               fillcolor="#F8FAFC" color="#CBD5E1" fontcolor="#0F1B38"]

    Underwriter [label="3 · Underwriter\\nPython (deterministic math)"
                 fillcolor="#EFF6FF" color="#BFDBFE" fontcolor="#1E3A5F"]

    Risk [label="4 · Risk Engine\\nRule Engine (Flags \\#1–\\#7) + Haiku"
          fillcolor="#FFF7ED" color="#FED7AA" fontcolor="#92400E"]

    Market [label="5 · Market Researcher\\nClaude Sonnet + optional Exa web search"
            fillcolor="#F0FDF4" color="#86EFAC" fontcolor="#166534"]

    Report [label="6 · Report Writer\\nClaude Opus — IC Memo drafting"
            fillcolor="#FDF4FF" color="#E9D5FF" fontcolor="#6B21A8"]

    Mem [label="Shared Memory\\n(results dict + Google Sheets history)"
         fillcolor="#FEFCE8" color="#FDE68A" fontcolor="#92400E" shape=cylinder]

    Verdict [label="IC Memo + GO / NO-GO Verdict\\n+ Deal History + Export"
             fillcolor="#DCFCE7" color="#86EFAC" fontcolor="#15803D" shape=note]

    OM       -> Orch
    Orch     -> Parser
    Parser   -> Extractor
    Extractor -> Underwriter
    Underwriter -> Risk
    Underwriter -> Market
    Risk    -> Report
    Market  -> Report
    Report  -> Verdict
    Extractor   -> Mem [style=dashed color="#D1D5DB" label="persist"]
    Underwriter -> Mem [style=dashed color="#D1D5DB"]
    Report      -> Mem [style=dashed color="#D1D5DB"]
}
"""

try:
    st.graphviz_chart(_DOT, use_container_width=True)
except Exception:
    # Fallback ASCII diagram when graphviz is unavailable in the environment
    st.markdown(
        """```
OM PDF
  ↓
Orchestrator (utils/pipeline.py)
  ↓
[1 · Parser — pdfplumber]
  ↓
[2 · Extractor — Claude Haiku]
  ↓
[3 · Underwriter — Python (deterministic)]
  ├──→ [4 · Risk Engine — Rule Engine #1–#7 + Haiku]
  └──→ [5 · Market Researcher — Claude Sonnet + Exa]
           ↓                              ↓
        [6 · Report Writer — Claude Opus]
                      ↓
       IC Memo + GO/NO-GO Verdict + History
        ↕
  Shared Memory (results dict + Google Sheets)
```""",
        unsafe_allow_html=False,
    )

st.caption(
    "**Stack:** AI/LLM (Claude Haiku · Sonnet · Opus) · "
    "Workflow (6-agent sequential pipeline) · "
    "UI (Streamlit) · "
    "Storage (JSONL deal history + optional Google Sheets)"
)
