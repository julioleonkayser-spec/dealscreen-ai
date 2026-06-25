"""Deal History page — cloud (Google Sheets) primary, local JSONL fallback."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.components import inject_css, page_header, empty_state
from utils.history import load_history, load_deals_from_sheet

inject_css()

page_header(
    "Deal History",
    "A log of every deal analyzed. Saved to Google Sheets (when configured) and locally.",
)

# ── Cloud Deal History (Google Sheets) ───────────────────────────────────────

sheets_df = load_deals_from_sheet()

if sheets_df is not None and not sheets_df.empty:
    st.markdown("#### ☁️ Cloud Deal History (Google Sheets)")
    st.success(
        f"☁️ **{len(sheets_df)} deal(s)** persisted to Google Sheets — "
        "history survives app restarts."
    )

    # Map common column names to friendly display names
    _col_rename = {
        "timestamp":        "Date",
        "property_name":    "Property",
        "market":           "Market",
        "dscr":             "DSCR",
        "cap_rate_inplace": "Cap Rate",
        "deal_score":       "Score",
        "score_label":      "Rating",
        "go_no_go":         "Verdict",
        "source_file":      "File",
    }
    _display_df = sheets_df.rename(columns=_col_rename)
    if "Date" in _display_df.columns:
        _display_df["Date"] = _display_df["Date"].astype(str).str[:10]

    st.dataframe(_display_df, use_container_width=True, hide_index=True)
    st.divider()

# ── Local Deal History (JSONL) ────────────────────────────────────────────────

entries = load_history(n=50)

# Nothing in either source → empty state
if not entries and (sheets_df is None or sheets_df.empty):
    empty_state(
        "📚",
        "No deals analyzed yet",
        "Screen a deal on the Screen Deal page to start building your deal history.",
    )
    st.stop()

if entries:
    if sheets_df is not None:
        st.markdown("#### 📁 Local Deal History (JSONL backup)")
    else:
        st.markdown("#### 📁 Local Deal History")
        st.caption(
            "💡 Configure Google Sheets in `.streamlit/secrets.toml` for cloud persistence "
            "across app restarts. See `.streamlit/secrets.example.toml` for the template."
        )

    # ── Filters ───────────────────────────────────────────────────────────────

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

    filtered = entries[:]

    if verdict_filter != "All":
        filtered = [e for e in filtered if e.get("go_no_go", "") == verdict_filter]

    if score_filter == "Strong (≥80)":
        filtered = [e for e in filtered if (e.get("deal_score") or -1) >= 80]
    elif score_filter == "Borderline (60–79)":
        filtered = [e for e in filtered if 60 <= (e.get("deal_score") or -1) < 80]
    elif score_filter == "Weak (<60)":
        filtered = [e for e in filtered if (e.get("deal_score") or 101) < 60]

    if not filtered:
        st.info("No deals match the selected filters.")
        st.stop()

    # ── Table ─────────────────────────────────────────────────────────────────

    _VERDICT_BG = {
        "Go":             "#d4edda",
        "No-Go":          "#f8d7da",
        "Conditional Go": "#fff3cd",
    }

    rows = []
    for e in filtered:
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
        f"Showing {len(filtered)} deal(s) — most recent first. "
        "🟢 Go · 🔴 No-Go · 🟡 Conditional Go"
    )
