# Agent 2: Financial Extractor Prompt Documentation

## Purpose
Extract structured CRE financial metrics from raw PDF text using Claude Haiku. Every extracted value is citation-anchored to a source page number.

## Model
`claude-haiku-4-5` — fast and cost-effective for structured extraction tasks.

## Inputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `parser_output` | dict | Output from `agents/parser.py` |
| `api_key` | string | Anthropic API key (optional, falls back to env var) |

## Outputs
```json
{
  "property_name": { "value": "The Oakwood", "confidence": 95, "source_page": 1, "flag": null },
  "location": { "value": "Austin, TX", "confidence": 90, "source_page": 1, "flag": null },
  "asset_class": { "value": "Multifamily", "confidence": 88, "source_page": 2, "flag": null },
  "units": { "value": 120, "confidence": 95, "source_page": 3, "flag": null },
  "asking_price": { "value": 18500000, "confidence": 92, "source_page": 4, "flag": null },
  "year_built": { "value": 1998, "confidence": 85, "source_page": 2, "flag": null },
  "occupancy_pct": { "value": 93.5, "confidence": 90, "source_page": 7, "flag": null },
  "noi_t12": { "value": 925000, "confidence": 88, "source_page": 10, "flag": null },
  "noi_proforma": { "value": 1050000, "confidence": 75, "source_page": 12, "flag": null },
  "asking_cap_rate": { "value": 5.0, "confidence": 95, "source_page": 4, "flag": null },
  "gross_potential_rent": { "value": 1560000, "confidence": 82, "source_page": 8, "flag": null }
}
```

## System Prompt
```
You are a commercial real estate financial analyst AI. Your job is to extract specific financial and property data from offering memorandum (OM) text.

CRITICAL RULES:
1. NEVER invent or estimate numbers that are not explicitly stated in the text.
2. Every extracted value MUST cite the page number where it was found.
3. If a value is not found anywhere in the document, set value=null, confidence=0, flag="missing".
4. Confidence score (0-100) reflects how clearly the value was stated, NOT how likely it exists.
   - 90-100: Explicitly labeled and unambiguous
   - 70-89: Stated but requires minor inference (e.g., totaling units from a rent roll)
   - 50-69: Implied or partially stated
   - 0-49: Not found or very unclear

Return ONLY a valid JSON object — no explanation, no markdown fences.
```

## User Prompt Template
```
Extract the following fields from this offering memorandum text. Return a single JSON object where each key maps to an object with:
  - "value": the extracted value (number, string, or null)
  - "confidence": integer 0-100
  - "source_page": page number where found (integer or null)
  - "flag": null if found, "missing" if not found

Fields to extract:
- property_name: string, the name or address of the property
- location: string, city/state/market
- asset_class: string, e.g. "Multifamily", "Office", "Retail", "Industrial", "Mixed-Use"
- units: integer, number of units/doors (for multifamily) or square feet (for commercial)
- asking_price: float, in dollars
- year_built: integer
- occupancy_pct: float, current physical occupancy as a percentage (e.g. 92.5)
- noi_t12: float, trailing 12-month Net Operating Income in dollars
- noi_proforma: float, projected/stabilized NOI in dollars
- asking_cap_rate: float, cap rate as a percentage (e.g. 5.25)
- gross_potential_rent: float, total gross potential rental income in dollars

DOCUMENT TEXT:
{document_text}
```

## Edge Cases Handled
| Scenario | Behavior |
|----------|----------|
| Missing field | `value=null, confidence=0, flag="missing"` |
| Claude returns invalid JSON | `extraction_error` key set with raw response |
| Document too long | Truncated at 80,000 chars with notice |
| API key not set | `extraction_error` key set |
| Parser error propagated | `extraction_error` key set |

## Confidence Scoring Guide
- **≥80 (green):** High-confidence extract, safe to use directly in calculations
- **50–79 (yellow):** Review before using in final underwriting
- **<50 (red):** Not found or unreliable — do not use in calculations

## Hard Rule
The LLM performs extraction only. All financial calculations (NOI verification, Cap Rate, DSCR, IRR, CoC) are performed deterministically in Python by Agent 3 (Calculator).
