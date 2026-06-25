"""Deal history persistence — append-only JSONL (always) + Google Sheets (when configured)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

HISTORY_FILE = Path(__file__).parent.parent / "outputs" / "deal_history.jsonl"

# ── Local JSONL (primary fallback) ────────────────────────────────────────────

def append_history_entry(entry: dict) -> None:
    """Write entry to JSONL and, if configured, to Google Sheets."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    # Best-effort cloud append — never raises
    append_deal_to_sheet(entry)


def load_history(n: int = 20) -> list:
    if not HISTORY_FILE.exists():
        return []
    lines = HISTORY_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in reversed(lines):
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
        if len(entries) >= n:
            break
    return entries


# ── Google Sheets (optional cloud layer) ──────────────────────────────────────

def get_deals_connection():
    """
    Return a GSheetsConnection if secrets are configured, else None.

    Secrets required in .streamlit/secrets.toml:
        [connections.deals_sheet]
        spreadsheet = "https://docs.google.com/spreadsheets/d/..."
        type        = "gsheets"
        # service-account JSON key fields below
        private_key_id = "..."
        private_key    = "-----BEGIN RSA PRIVATE KEY-----\\n..."
        client_email   = "...@....iam.gserviceaccount.com"
        ...
    """
    try:
        from streamlit_gsheets import GSheetsConnection  # type: ignore
        import streamlit as st

        secrets = st.secrets  # raises FileNotFoundError if no secrets.toml
        if "connections" not in secrets:
            return None
        if "deals_sheet" not in secrets["connections"]:
            return None
        return st.connection("deals_sheet", type=GSheetsConnection)
    except Exception:
        return None


def append_deal_to_sheet(record: dict) -> None:
    """
    Append a single deal record to the 'Sheet1' worksheet.
    Best-effort — silently swallows all errors so the app never crashes.
    """
    try:
        import pandas as pd

        conn = get_deals_connection()
        if conn is None:
            return

        existing = conn.read(worksheet="Sheet1", ttl=0)
        new_row  = pd.DataFrame([record])

        if existing is None or existing.empty:
            updated = new_row
        else:
            updated = pd.concat([existing, new_row], ignore_index=True)

        conn.update(worksheet="Sheet1", data=updated)
    except Exception:
        pass


def load_deals_from_sheet():
    """
    Load the deal history DataFrame from Google Sheets.
    Returns a DataFrame, or None if Sheets is not configured / unavailable.
    """
    try:
        conn = get_deals_connection()
        if conn is None:
            return None

        import pandas as pd

        df = conn.read(worksheet="Sheet1", ttl=30)
        if df is None or df.empty:
            return None
        return df
    except Exception:
        return None
