"""Compare Deals page — side-by-side analysis of 2–3 OMs."""

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.components import inject_css, page_header, empty_state
from utils.formatters import fmt_compare
from utils.pipeline import compute_winner, file_hash, get_compare_value, run_comparison_pipeline

inject_css()

api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")

# ── Page header ───────────────────────────────────────────────────────────────

page_header(
    "Compare Deals",
    "Upload 2–3 Offering Memoranda to run a side-by-side financial comparison.",
)

if not api_key:
    st.error("ANTHROPIC_API_KEY not configured. Add it in .env or Streamlit Secrets.")
    st.stop()

# ── Upload ────────────────────────────────────────────────────────────────────

st.caption(
    "Runs Parser → Extractor → Underwriter on each file. "
    "Market Research and Report Writer are skipped for speed."
)

uploaded_files = st.file_uploader(
    "Upload 2–3 Offering Memoranda (PDF)",
    type=["pdf"],
    accept_multiple_files=True,
    key="compare_uploader",
    label_visibility="collapsed",
)

if not uploaded_files:
    empty_state(
        "⚖️",
        "No documents uploaded yet",
        "Upload 2–3 PDF Offering Memoranda above to begin the side-by-side comparison.",
    )
    st.stop()

if len(uploaded_files) > 3:
    st.warning("Maximum 3 files — using the first 3.")
    uploaded_files = uploaded_files[:3]

if len(uploaded_files) < 2:
    st.info("Upload at least one more PDF to enable the comparison.")
    st.stop()

# ── Run or use cached comparison pipeline ────────────────────────────────────

file_data   = [(f.name, f.read()) for f in uploaded_files]
file_hashes = sorted(file_hash(b) for _, b in file_data)

if (
    st.session_state.get("comp_hashes") == file_hashes
    and "comp_results" in st.session_state
):
    deal_results = st.session_state["comp_results"]
else:
    deal_results = []
    total        = len(file_data)
    bar          = st.progress(0, text="Starting comparison pipeline…")
    for i, (fname, fbytes) in enumerate(file_data):
        bar.progress(i / total, text=f"Processing {fname}…")
        deal_results.append(run_comparison_pipeline(fbytes, fname, api_key))
    bar.progress(1.0, text="All files processed.")
    st.session_state["comp_results"] = deal_results
    st.session_state["comp_hashes"]  = file_hashes

winner_idx = compute_winner(deal_results)

# ── Column headers ─────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)

header_cols = st.columns(len(deal_results))
for i, (col, r) in enumerate(zip(header_cols, deal_results)):
    prop  = get_compare_value(r, "extracted", "property_name") or r["filename"]
    badge = '<span class="ds-winner-badge">🏆 Best</span>' if i == winner_idx else ""
    if r.get("error"):
        col.error(f"❌ **{r['filename']}**\n\n{r['error']}")
    else:
        col.markdown(
            f'<div style="font-weight:700;font-size:15px;color:#0F1B38;">'
            f'{prop}{badge}</div>'
            f'<div style="font-size:12px;color:#94A3B8;margin-top:2px;">{r["filename"]}</div>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<hr style="border:none;border-top:1px solid #E8EDF5;margin:14px 0 20px;">',
    unsafe_allow_html=True,
)

# ── Comparison table ───────────────────────────────────────────────────────────

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

col_names    = [
    get_compare_value(r, "extracted", "property_name") or r["filename"]
    for r in deal_results
]
display_data = {}
numeric_data = {}
higher_map   = {}

for label, source, key, higher in COMPARE_METRICS:
    disp_vals, num_vals = [], []
    for r in deal_results:
        raw = get_compare_value(r, source, key)
        disp_vals.append(fmt_compare(key, raw))
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
    "🟢 Bold = best value per metric · 🔴 = weakest value · "
    "🏆 Best = highest combined DSCR + Cap Rate score"
)

# ── AI-style summary ───────────────────────────────────────────────────────────

if winner_idx >= 0:
    winner_name = get_compare_value(deal_results[winner_idx], "extracted", "property_name") \
                  or deal_results[winner_idx]["filename"]
    winner_dscr = get_compare_value(deal_results[winner_idx], "underwriter", "dscr")
    winner_cap  = get_compare_value(deal_results[winner_idx], "underwriter", "cap_rate_inplace")

    dscr_str = f"DSCR of {winner_dscr:.2f}x" if winner_dscr else "DSCR not available"
    cap_str  = f"cap rate of {winner_cap:.2f}%" if winner_cap else "cap rate not available"

    st.markdown(
        f'<div style="background:#EEF4FF;border:1px solid #C7D9F8;border-left:4px solid #1B3A6B;'
        f'border-radius:8px;padding:16px 20px;margin-top:20px;">'
        f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;'
        f'color:#1B3A6B;margin-bottom:6px;">Preferred Deal</div>'
        f'<div style="font-size:14px;font-weight:600;color:#0F1B38;margin-bottom:4px;">{winner_name}</div>'
        f'<div style="font-size:13px;color:#475569;line-height:1.6;">'
        f'Scores highest on a combined DSCR + cap rate basis ({dscr_str}, {cap_str}). '
        f'Always verify against primary source documents before proceeding.'
        f'</div></div>',
        unsafe_allow_html=True,
    )
