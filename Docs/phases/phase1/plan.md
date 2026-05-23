# Phase 1 — Foundation & Review Ingestion

## Goal
Establish the project foundation and build a reliable, repeatable mechanism to load raw app store reviews and prepare them for AI analysis.

---

## Context & Rationale

The entire pipeline depends on having clean, normalized review data. App Store and Play Store exports use different field names, encodings, and date formats — so a dedicated normalization layer is essential before any analysis begins. We handle this as Phase 1 because every downstream component depends on its output.

We deliberately limit the ingestion source to **official CSV exports only** (from App Store Connect and Google Play Console). This is a hard constraint: no scraping, no third-party review aggregators, no login-based access. This keeps us legally compliant with Apple and Google's terms of service and ensures the data is stable and structured.

---

## What We Are Building

### Unified Review Schema
Both store exports are mapped to a single normalized format:
```json
{
  "id": "string",
  "rating": "1–5",
  "title": "string",
  "text": "string",
  "date": "ISO8601",
  "source": "appstore | playstore"
}
```
The `source` field distinguishes App Store vs Play Store records for downstream filtering if needed.

### Date-Range Filtering
The agent is configurable to pull the last 8 or 12 weeks of reviews. This window is set in the agent's run configuration, not hardcoded. The default is 8 weeks. The `reference_date` parameter makes the filter fully testable without depending on wall-clock time.

### Data Quality Handling
- Reviews with missing text fields are excluded
- Duplicate records deduplicated by review ID or content fingerprint (SHA-256 of `rating + title + text + date`)
- Character encoding normalized to UTF-8 (invalid bytes replaced, not dropped)
- Rows with unparseable dates or out-of-range ratings are skipped with a warning logged

### No PII at Ingestion
Reviewer usernames and user IDs — if present in export fields — are excluded from the normalized output at this layer. We do not need them for any downstream analysis. A PII field guard (`assert_no_pii_fields`) runs as a belt-and-suspenders check after normalization.

---

## Folder Structure (Phase 1 output)

```
MCP/
├── ingestion/
│   ├── __init__.py          ← public API: load_reviews()
│   ├── schema.py            ← Review dataclass + fingerprint()
│   ├── parsers.py           ← App Store + Play Store CSV parsers
│   ├── filters.py           ← date filter, dedup, PII guard
│   ├── loader.py            ← main entry point
│   └── sample_data/
│       ├── appstore_sample.csv
│       └── playstore_sample.csv
├── ingestion/output/
│   └── reviews.json         ← normalized output from run_phase1.py
├── run_phase1.py            ← Phase 1 runner script
└── tests/
    └── test_ingestion.py    ← 16 tests covering all 9 eval.md Phase 1 cases
```

---

## Key Decisions Made at This Phase

| Decision | Rationale | Ref |
|---|---|---|
| Official CSV exports only, no scraping | Legal compliance with Apple/Google ToS | D-002 |
| Both sources normalized into one schema | Downstream modules work on one format | — |
| Date range configurable via `--weeks` | Supports flexible re-runs and testing | — |
| Content fingerprint for deduplication | Handles cases where source ID is absent | — |

---

## Deliverables

- [x] `ingestion/` module: parsers, normalization, deduplication, date filtering
- [x] `ingestion/sample_data/` — 15 synthetic reviews per store (30 total)
- [x] `ingestion/output/reviews.json` — normalized output from Phase 1 run
- [x] `run_phase1.py` — Phase 1 runner with console summary and JSON output
- [x] `tests/test_ingestion.py` — all 9 eval.md Phase 1 test cases passing (16 tests total)

---

## Status

**Phase 1: COMPLETE**
- 16/16 tests passing
- 30 reviews ingested (15 App Store + 15 Play Store)
- Output written to `ingestion/output/reviews.json`
- No PII in output (field audit passed)
- Ready to hand off to Phase 2 (Theme Analyzer)
