"""Agent 5: Market Researcher — Claude Sonnet synthesizes CRE submarket context."""

import json
import os
import sys
import urllib.request
import urllib.error

SYSTEM_PROMPT = """You are a commercial real estate market analyst with deep expertise in US property markets.

You will be given a property's location, asset class, and asking cap rate. Synthesize your knowledge into a structured market assessment.

RULES:
1. Ground every claim in what is known about that metro/submarket — no generic filler.
2. The cap_rate_benchmark must be a specific range (e.g., "5.5%–6.5%"), not a vague statement.
3. deal_positioning must be one of exactly: "below market", "at market", "above market".
4. rent_growth_trend direction must be one of exactly: "positive", "flat", "negative".
5. Return ONLY valid JSON — no markdown fences, no explanation.
6. Always include exactly this footer field: "AI-synthesized — verify with CoStar/Crexi"."""

RESEARCH_PROMPT = """Analyze this CRE deal's market context and return a JSON object with these exact fields:

- "submarket_summary": string — 2-3 sentences describing the submarket, demand drivers, and current conditions
- "cap_rate_benchmark": string — typical cap rate range for this asset class in this market (e.g. "5.0%–6.0%")
- "rent_growth_trend": object with:
    - "direction": "positive" | "flat" | "negative"
    - "reason": string — one sentence explaining the trend
- "deal_positioning": "below market" | "at market" | "above market" — vs the cap_rate_benchmark
- "footer": "AI-synthesized — verify with CoStar/Crexi"
- "researcher_error": null

Deal inputs:
- Location: {location}
- Asset class: {asset_class}
- Asking cap rate: {asking_cap_rate}"""


def _web_search_exa(query: str, exa_api_key: str) -> list[str]:
    """
    Call the Exa search API and return 2–3 short bullet strings summarising results.
    Raises on HTTP/network error so the caller can catch and fall back gracefully.
    """
    url = "https://api.exa.ai/search"
    payload = json.dumps({
        "query": query,
        "numResults": 3,
        "useAutoprompt": True,
        "contents": {"text": {"maxCharacters": 350}},
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "x-api-key": exa_api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    bullets: list[str] = []
    for result in (data.get("results") or [])[:3]:
        text = (
            (result.get("text") or "").strip()
            or (result.get("highlights") or [""])[0].strip()
            or (result.get("title") or "").strip()
        )
        if text:
            bullets.append(f"• {text[:300]}")
    return bullets


def research_market(extracted: dict, api_key=None, use_web_search: bool = False, exa_api_key: str | None = None) -> dict:
    """
    Generate submarket context for a CRE deal using Claude Sonnet.

    Args:
        extracted:       Output from the Extractor agent.
        api_key:         Anthropic API key.
        use_web_search:  When True, call Exa search for live market notes before Sonnet.
        exa_api_key:     Exa API key (required when use_web_search=True).

    Returns:
        {
            "submarket_summary": str,
            "cap_rate_benchmark": str,
            "rent_growth_trend": { "direction": str, "reason": str },
            "deal_positioning": str,
            "footer": "AI-synthesized — verify with CoStar/Crexi",
            "researcher_error": None | str,
            "web_search_notes": list[str] | None,
        }
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return _error("ANTHROPIC_API_KEY not set.")

    def get(field):
        entry = extracted.get(field)
        if isinstance(entry, dict):
            return entry.get("value")
        return None

    location = get("location") or "Unknown location"
    asset_class = get("asset_class") or "Unknown asset class"
    asking_cap_rate = get("asking_cap_rate")
    cap_rate_str = f"{asking_cap_rate:.2f}%" if asking_cap_rate else "not provided"

    # ── Optional: Exa live web search ─────────────────────────────────────────
    web_search_notes: list[str] | None = None
    web_search_status: str | None = None
    if use_web_search and exa_api_key:
        search_query = (
            f"{asset_class} cap rates rent growth {location} 2024 2025 commercial real estate"
        )
        try:
            bullets = _web_search_exa(search_query, exa_api_key)
            if bullets:
                web_search_notes = bullets
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as exc:
            web_search_status = f"Live search unavailable: {exc}"
    elif use_web_search and not exa_api_key:
        web_search_status = "Live search unavailable: EXA_API_KEY not configured."

    try:
        import anthropic
    except ImportError:
        return _error("anthropic package not installed.")

    # Inject live market notes into the prompt when available
    live_notes_block = ""
    if web_search_notes:
        joined = "\n".join(web_search_notes)
        live_notes_block = (
            f"\n\nLive market notes (from web search — use these as grounding context):\n{joined}\n"
        )

    user_msg = RESEARCH_PROMPT.format(
        location=location,
        asset_class=asset_class,
        asking_cap_rate=cap_rate_str,
    ) + live_notes_block

    try:
        client = anthropic.Anthropic(api_key=key)
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:
        return _error(f"API call failed: {e}")

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:]).rstrip("`").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        return _error(f"Claude returned invalid JSON: {e}", raw_response=raw)

    _enforce_research_schema(result)
    result["web_search_notes"] = web_search_notes
    if web_search_status:
        result["web_search_status"] = web_search_status
    return result


def _error(msg: str, raw_response: str = None) -> dict:
    out = {
        "submarket_summary": None,
        "cap_rate_benchmark": None,
        "rent_growth_trend": {"direction": None, "reason": None},
        "deal_positioning": None,
        "footer": "AI-synthesized — verify with CoStar/Crexi",
        "researcher_error": msg,
    }
    if raw_response:
        out["raw_response"] = raw_response
    return out


def _enforce_research_schema(data: dict) -> None:
    """Ensure required keys exist; mutate in place."""
    data.setdefault("submarket_summary", None)
    data.setdefault("cap_rate_benchmark", None)
    data.setdefault("rent_growth_trend", {"direction": None, "reason": None})
    data.setdefault("deal_positioning", None)
    data["footer"] = "AI-synthesized — verify with CoStar/Crexi"
    data.setdefault("researcher_error", None)

    trend = data["rent_growth_trend"]
    if not isinstance(trend, dict):
        data["rent_growth_trend"] = {"direction": str(trend), "reason": None}
    else:
        trend.setdefault("direction", None)
        trend.setdefault("reason", None)

    valid_positioning = {"below market", "at market", "above market"}
    if data["deal_positioning"] not in valid_positioning:
        data["deal_positioning"] = None

    valid_directions = {"positive", "flat", "negative"}
    if data["rent_growth_trend"]["direction"] not in valid_directions:
        data["rent_growth_trend"]["direction"] = None


if __name__ == "__main__":
    sys.path.insert(0, __import__("pathlib").Path(__file__).parent.parent.__str__())
    from dotenv import load_dotenv
    load_dotenv()

    sample = {
        "location":       {"value": "Austin, TX", "confidence": 90, "source_page": 1, "flag": None},
        "asset_class":    {"value": "Multifamily", "confidence": 88, "source_page": 1, "flag": None},
        "asking_cap_rate":{"value": 4.5,           "confidence": 92, "source_page": 4, "flag": None},
    }
    result = research_market(sample)
    print(json.dumps(result, indent=2))
