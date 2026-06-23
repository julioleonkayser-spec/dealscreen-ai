"""Core pipeline orchestration — no UI dependencies."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Callable, Optional

from agents.extractor import extract_financials
from agents.market_researcher import research_market
from agents.parser import parse_pdf
from agents.report_writer import write_report
from agents.risk_flagger import flag_risks
from agents.underwriter import underwrite


def file_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def run_pipeline(
    file_bytes: bytes,
    api_key: str,
    on_step: Optional[Callable[[str, str], None]] = None,
) -> dict:
    """
    Run all 6 agents sequentially.

    on_step(stage_name, display_message) is called at each stage transition.
    Returns a results dict with keys: parsed, extracted, underwriter, risk, market, report.
    """

    def step(name: str, msg: str) -> None:
        if on_step:
            on_step(name, msg)

    results = {}

    step("Parser", "Parsing PDF document…")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        parsed = parse_pdf(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if parsed["error"]:
        results["parse_error"] = parsed["error"]
        return results
    results["parsed"] = parsed

    step("Extractor", "Extracting financial data with Claude Haiku…")
    extracted = extract_financials(parsed, api_key=api_key or None)
    results["extracted"] = extracted
    if "extraction_error" in extracted:
        return results

    step("Underwriter", "Running deterministic underwriting calculations…")
    uw = underwrite(extracted)
    results["underwriter"] = uw

    step("Risk Flagger", "Evaluating risk flags…")
    risk = flag_risks(extracted, uw, api_key=api_key or None)
    results["risk"] = risk

    step("Market Research", "Synthesizing market context with Claude Sonnet…")
    market = research_market(extracted, api_key=api_key or None)
    results["market"] = market

    step("Report Writer", "Writing Investment Committee Memo with Claude Opus…")
    report = write_report(
        {
            "extractor": extracted,
            "underwriter": uw,
            "risk_flagger": risk,
            "market_researcher": market,
        },
        api_key=api_key or None,
    )
    results["report"] = report

    return results


def run_comparison_pipeline(file_bytes: bytes, filename: str, api_key: str) -> dict:
    """Run Parser → Extractor → Underwriter only (no AI memo generation)."""
    result = {"filename": filename, "error": None, "extracted": None, "underwriter": None}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        parsed = parse_pdf(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if parsed["error"]:
        result["error"] = parsed["error"]
        return result

    extracted = extract_financials(parsed, api_key=api_key or None)
    if "extraction_error" in extracted:
        result["error"] = extracted["extraction_error"]
        return result

    result["extracted"] = extracted
    result["underwriter"] = underwrite(extracted)
    return result


def get_compare_value(result: dict, source: str, key: str):
    if result.get("error"):
        return None
    if source == "extracted":
        entry = result.get("extracted", {}).get(key)
        return entry.get("value") if isinstance(entry, dict) else None
    if source == "underwriter":
        return result.get("underwriter", {}).get("metrics", {}).get(key, {}).get("value")
    return None


def compute_winner(results: list) -> int:
    scores = []
    for r in results:
        dscr = get_compare_value(r, "underwriter", "dscr") or 0.0
        cap  = get_compare_value(r, "underwriter", "cap_rate_inplace") or 0.0
        scores.append(
            max(0.0, (dscr - 0.8) / (2.0 - 0.8)) +
            max(0.0, (cap  - 3.0) / (10.0 - 3.0))
        )
    return -1 if all(s == 0.0 for s in scores) else scores.index(max(scores))
