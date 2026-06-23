# PD Hackathon — AI Deal Screening Agent

## Goal

Automate the first-pass underwriting of commercial real estate (CRE) deals submitted as PDF offering memoranda (OMs). The agent pipeline extracts raw financials, validates them against industry benchmarks, flags red flags, and produces a go/no-go screening report — in seconds, not hours.

**Hackathon:** Project Destined AI Agents x CRE Investments, June 2026 | $3,000 prize

---

## 6-Agent Pipeline Architecture

```
PDF Upload
    │
    ▼
[Agent 1] Parser          — pdfplumber, page-by-page text extraction
    │
    ▼
[Agent 2] Extractor       — Claude Haiku, structured JSON financials
    │
    ▼
[Agent 3] Calculator      — deterministic NOI/Cap/DSCR/IRR/CoC formulas
    │
    ▼
[Agent 4] Benchmarker     — compare metrics vs. market comps
    │
    ▼
[Agent 5] Red-Flag Hunter — contradiction detection, missing data warnings
    │
    ▼
[Agent 6] Reporter        — narrative deal memo + go/no-go verdict
    │
    ▼
Streamlit Dashboard + Downloadable PDF
```

### Agent Responsibilities

| Agent | Model | Input | Output |
|-------|-------|-------|--------|
| Parser | pdfplumber (deterministic) | PDF file | `{page_num: text}` dict |
| Extractor | claude-haiku-4-5 | page dict | structured JSON with citations |
| Calculator | Python (deterministic) | extracted JSON | computed metrics dict |
| Benchmarker | claude-haiku-4-5 | metrics + asset class | benchmark deltas |
| Red-Flag Hunter | claude-haiku-4-5 | all prior outputs | flagged issues list |
| Reporter | claude-sonnet-4-6 | all prior outputs | deal memo markdown |

---

## Tech Stack

| Layer | Library |
|-------|---------|
| PDF parsing | `pdfplumber` |
| AI inference | `anthropic` SDK (Haiku for extraction, Sonnet for reporting) |
| Web UI | `streamlit` |
| Data | `pandas` |
| Config | `python-dotenv` |
| Output | `reportlab` (PDF export) |

---

## CRE Financial Formulas

### Net Operating Income (NOI)
```
NOI = Gross Potential Rent
    - Vacancy & Credit Loss
    - Operating Expenses (excl. debt service)
```

### Capitalization Rate
```
Cap Rate = NOI / Current Market Value
```
*A higher cap rate = higher yield but higher perceived risk.*

### Debt Service Coverage Ratio (DSCR)
```
DSCR = NOI / Annual Debt Service
```
*Lenders typically require DSCR ≥ 1.25x.*

### Internal Rate of Return (IRR)
```
Solve for r in: 0 = Σ [CF_t / (1+r)^t]  for t = 0 to N
```
*Target varies by risk profile: Core 6-8%, Value-Add 10-14%, Opportunistic 15%+.*

### Cash-on-Cash Return
```
CoC = Annual Pre-Tax Cash Flow / Total Cash Invested
```

### Loss to Lease
```
Loss to Lease = (Market Rent - In-Place Rent) × Units
```
*Represents upside potential in value-add plays.*

---

## Hard Rules

1. **Every extracted number must cite its source page number.** Never hallucinate financial values. If a number is not found in the document, set `value=null`, `confidence=0`, `flag="missing"`.
2. All deterministic calculations (NOI, Cap Rate, DSCR, etc.) are computed in Python — never asked of the LLM.
3. The LLM's job is extraction and narrative, not arithmetic.
4. Red flags are surfaced to the user; the agent never suppresses them.
5. No PII from uploaded documents is stored beyond the session.

---

## File Structure

```
pd-hackathon/
├── agents/
│   ├── parser.py         # Agent 1: PDF → page dict
│   ├── extractor.py      # Agent 2: page dict → structured JSON
│   ├── calculator.py     # Agent 3: JSON → computed metrics
│   ├── benchmarker.py    # Agent 4: metrics → benchmark deltas
│   ├── red_flag.py       # Agent 5: all outputs → flagged issues
│   └── reporter.py       # Agent 6: all outputs → deal memo
├── uploads/              # Temp storage for uploaded PDFs
├── outputs/              # Generated reports
├── prompts/
│   ├── parser_prompt.md
│   ├── extractor_prompt.md
│   ├── benchmarker_prompt.md
│   ├── red_flag_prompt.md
│   └── reporter_prompt.md
├── app.py                # Streamlit web UI
├── CLAUDE.md             # This file
├── requirements.txt
└── .env.example
```

---

## Running the App

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Launch
streamlit run app.py
```
