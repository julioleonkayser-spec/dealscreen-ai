"""Deal History page — table of analyzed deals with filters."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.components import inject_css, page_header, empty_state
from utils.history import load_history

inject_css()

page_header(
    "Deal History",
    "A log of every deal analyzed in this session. Saved automatically after each full pipeline run.",
)

entries = load_history(n=50)

if not entries:
    empty_state(
        "📚",
        "No deals analyzed yet",
        "Screen a deal on the Screen Deal page to start building your deal history.",
    )
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────

filter_col1, filter_col2, _ = st.columns([1, 1, 3])

with filter_col1:
    verdict_filter = st.selectbox(
        "Filter by verdict",
        ["All", "Go", "No-Go", "Conditional Go", "Unknown"],
    )

with filter_col2:
    score_filter = st.selectbox(
        "Filter by score",
        ["All", "Strong (≥80)", "Borderline (60–79)", "Weak (<60)"],
    )

if verdict_filter != "All":
    entries = [e for e in entries if e.get("go_no_go", "") == verdict_filter]

if score_filter == "Strong (≥80)":
    entries = [e for e in entries if (e.get("deal_score") or -1) >= 80]
elif score_filter == "Borderline (60–79)":
    entries = [e for e in entries if 60 <= (e.get("deal_score") or -1) < 80]
elif score_filter == "Weak (<60)":
    entries = [e for e in entries if (e.get("deal_score") or 101) < 60]

if not entries:
    st.info("No deals match the selected filters.")
    st.stop()

# ── Table ─────────────────────────────────────────────────────────────────────

_VERDICT_BG = {
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
        "Score":     f"{e['deal_score']:.0f}"         if e.get("deal_score")       is not None else "—",
        "Rating":    e.get("score_label", "—"),
        "DSCR":      f"{e['dscr']:.2f}x"              if e.get("dscr")             is not None else "—",
        "Cap Rate":  f"{e['cap_rate_inplace']:.2f}%"  if e.get("cap_rate_inplace") is not None else "—",
        "Verdict":   e.get("go_no_go", "—"),
        "File":      e.get("source_file", "—"),
    })

df = pd.DataFrame(rows)

def verdict_row_style(row):
    bg = _VERDICT_BG.get(row["Verdict"], "")
    return [f"background-color: {bg}" if bg else ""] * len(row)

st.dataframe(
    df.style.apply(verdict_row_style, axis=1),
    use_container_width=True,
    hide_index=True,
)
st.caption(
    f"Showing {len(entries)} deal(s) — most recent first. "
    "🟢 Go · 🔴 No-Go · 🟡 Conditional Go"
)
