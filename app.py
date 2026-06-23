"""DealScreen AI — entry point. Defines multipage navigation."""

import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # local dev only; no-ops on Streamlit Cloud

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="DealScreen AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar branding (above navigation links) ─────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 4px 0 16px;">
          <div style="font-size:17px;font-weight:900;color:#0F1B38;letter-spacing:-.02em;">
            🏢 DealScreen AI
          </div>
          <div style="font-size:11px;color:#94A3B8;margin-top:3px;font-weight:500;">
            CRE Deal Screening Agent
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

# ── Navigation ────────────────────────────────────────────────────────────────

pg = st.navigation(
    [
        st.Page("pages/home.py",         title="Home",         icon="🏠", default=True),
        st.Page("pages/screen_deal.py",  title="Screen Deal",  icon="📋"),
        st.Page("pages/compare_deals.py",title="Compare Deals",icon="⚖️"),
        st.Page("pages/deal_history.py", title="Deal History", icon="📊"),
        st.Page("pages/settings.py",     title="Settings",     icon="⚙️"),
    ]
)

pg.run()
