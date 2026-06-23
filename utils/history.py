"""Deal history persistence — append-only JSONL in outputs/."""

import json
from pathlib import Path

HISTORY_FILE = Path(__file__).parent.parent / "outputs" / "deal_history.jsonl"


def append_history_entry(entry: dict) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


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
