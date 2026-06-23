# Agent 1: Parser Prompt Documentation

## Purpose
Deterministic PDF text extraction — no LLM involved. This agent runs pdfplumber and returns structured page-by-page text for downstream agents.

## Inputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | string | Absolute or relative path to a `.pdf` file |

## Outputs
```json
{
  "pages": {
    "1": "Full text of page 1...",
    "2": "Full text of page 2..."
  },
  "full_text": "--- PAGE 1 ---\n...\n\n--- PAGE 2 ---\n...",
  "page_count": 42,
  "error": null
}
```

## Edge Cases Handled
| Scenario | Behavior |
|----------|----------|
| File not found | `error` field set, `pages` empty |
| Non-PDF file | `error` field set |
| Scanned/image-only page | Page text set to `[PAGE N: NO EXTRACTABLE TEXT — may be scanned/image-only]` |
| Page extraction failure | Page text set to `[PAGE N EXTRACTION ERROR: ...]` |
| Empty PDF | `error` field set |
| pdfplumber not installed | `error` field set with install instructions |

## Notes
- Page numbers in output are 1-indexed (matching the PDF's page numbering)
- No LLM calls are made in this agent
- The `full_text` field includes `--- PAGE N ---` delimiters so downstream agents can parse source page references
