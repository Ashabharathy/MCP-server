# Phase 1 — Evaluation & Exit Criteria

## Test Scope
- Parser correctness for App Store and Play Store CSV formats
- Date-range filtering
- Schema normalization and data quality

---

## Test Cases

| ID | Test Case | Expected Result | Status |
|---|---|---|---|
| P1-T1 | Parse valid App Store CSV export | All records normalized to `{ id, rating, title, text, date, source }` | ✅ PASS |
| P1-T2 | Parse valid Play Store CSV export | All records normalized correctly | ✅ PASS |
| P1-T3 | Apply 8-week date filter | Only reviews within last 8 weeks returned | ✅ PASS |
| P1-T4 | Apply 12-week date filter | Only reviews within last 12 weeks returned | ✅ PASS |
| P1-T5 | Duplicate reviews in input | Deduplication removes duplicates; unique set returned | ✅ PASS |
| P1-T6 | Missing fields in CSV row | Row skipped or defaulted gracefully; no crash | ✅ PASS |
| P1-T7 | Non-UTF-8 encoded characters | Handled without crash; characters sanitized | ✅ PASS |
| P1-T8 | Empty CSV file | Returns empty list; no crash | ✅ PASS |
| P1-T9 | 0 reviews in date range | Returns empty list; pipeline handles gracefully | ✅ PASS |

---

## Additional Tests (Integration)

| ID | Test Case | Status |
|---|---|---|
| P1-I1 | `load_reviews` merges both sources with correct dedup | ✅ PASS |
| P1-I2 | `load_reviews` raises `ValueError` if no paths provided | ✅ PASS |
| P1-I3 | `load_reviews` raises `FileNotFoundError` for missing file | ✅ PASS |
| P1-I4 | PII field audit: no `username`, `user_id`, `email` on Review objects | ✅ PASS |

**Total: 16/16 tests passing**

Run command:
```
py -m pytest tests/test_ingestion.py -v
```

---

## Exit Criteria

- [x] All 9 core test cases pass
- [x] Parser handles both CSV formats without manual intervention
- [x] No PII fields in normalized output (verified by field audit)
- [x] Code reviewed and merged

---

## Phase 1 Exit Status: **COMPLETE**

Date completed: 2026-05-22
Output artifact: `ingestion/output/reviews.json` (30 reviews, dual-source, zero PII)
