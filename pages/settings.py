"""Settings / About page."""

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.components import inject_css, page_header, render_pipeline_reliability

inject_css()

page_header("Settings & About", "Application metadata, configuration status, and legal disclaimer.")

# ── Configuration status ──────────────────────────────────────────────────────

api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
key_ok  = bool(api_key)

st.markdown(
    """
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                letter-spacing:.08em;color:#94A3B8;margin-bottom:12px;">
      Configuration
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        f"""<div class="ds-info-card">
          <div class="ds-info-label">API Key</div>
          <div class="ds-info-value">{"✅ Configured" if key_ok else "❌ Not found"}</div>
          <div class="ds-info-sub">
            {"ANTHROPIC_API_KEY is set and ready." if key_ok
             else "Set ANTHROPIC_API_KEY in .env (local) or Streamlit Secrets (cloud)."}
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """<div class="ds-info-card">
          <div class="ds-info-label">Pipeline Models</div>
          <div class="ds-info-value">Claude Haiku · Sonnet · Opus</div>
          <div class="ds-info-sub">
            Extractor &amp; Risk Flagger use Haiku.
            Market Researcher uses Sonnet.
            Report Writer uses Opus.
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Application metadata ──────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                letter-spacing:.08em;color:#94A3B8;margin-bottom:12px;">
      About
    </div>
    """,
    unsafe_allow_html=True,
)

c3, c4, c5 = st.columns(3)
with c3:
    st.markdown(
        """<div class="ds-info-card">
          <div class="ds-info-label">Application</div>
          <div class="ds-info-value">DealScreen AI</div>
          <div class="ds-info-sub">CRE Deal Screening Agent</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        """<div class="ds-info-card">
          <div class="ds-info-label">Version</div>
          <div class="ds-info-value">2.0.0</div>
          <div class="ds-info-sub">Multipage · Premium UI</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c5:
    st.markdown(
        """<div class="ds-info-card">
          <div class="ds-info-label">Context</div>
          <div class="ds-info-value">Project Destined</div>
          <div class="ds-info-sub">AI Agents × CRE Hackathon · June 2026</div>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Pipeline overview ─────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                letter-spacing:.08em;color:#94A3B8;margin-bottom:12px;">
      6-Agent Pipeline
    </div>
    """,
    unsafe_allow_html=True,
)

AGENTS = [
    ("1. Parser",         "pdfplumber",        "PDF → page text",                   "Deterministic"),
    ("2. Extractor",      "Claude Haiku",       "Page text → structured JSON",       "AI extraction"),
    ("3. Underwriter",    "Python formulas",    "JSON → Cap Rate, DSCR, CoC…",       "Deterministic"),
    ("4. Risk Flagger",   "Claude Haiku",       "Metrics → enriched risk flags",     "Hybrid"),
    ("5. Market Research","Claude Sonnet",      "Location → submarket context",      "AI synthesis"),
    ("6. Report Writer",  "Claude Opus",        "All outputs → IC Memo markdown",    "AI narrative"),
]

df = pd.DataFrame(AGENTS, columns=["Agent", "Model", "Function", "Type"])
st.dataframe(df, use_container_width=True, hide_index=True)

# ── Pipeline Reliability ──────────────────────────────────────────────────────

render_pipeline_reliability()

# ── Disclaimer ────────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="background:#FFF8F0;border:1px solid #FED7AA;border-radius:10px;padding:18px 20px;">
      <div style="font-size:12px;font-weight:700;color:#92400E;text-transform:uppercase;
                  letter-spacing:.06em;margin-bottom:8px;">⚠️ Legal Disclaimer</div>
      <div style="font-size:13px;color:#78350F;line-height:1.65;">
        DealScreen AI is a <strong>decision-support tool only</strong> and does not constitute
        investment advice. All AI-generated analysis — including metrics, risk flags, market
        assessments, and IC Memo verdicts — must be independently verified against primary
        source documents by qualified real estate and financial professionals before any
        investment decision is made. Market research is AI-synthesized and should be
        cross-referenced with CoStar, Crexi, or equivalent data sources.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
