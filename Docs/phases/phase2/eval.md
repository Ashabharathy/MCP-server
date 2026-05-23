# Phase 2 — Evaluation & Exit Criteria

## Test Scope
- LLM clustering accuracy
- Theme count enforcement (≤ 5)
- Quote extraction quality
- PII removal from quotes

---

## Test Cases

| ID | Test Case | Expected Result | Status |
|---|---|---|---|
| P2-T1 | 50 mixed reviews across 5 topics | ≤ 5 themes returned, each theme labelled | ⬜ PENDING |
| P2-T2 | 10 reviews all about KYC | 1 theme returned (not inflated to 5) | ⬜ PENDING |
| P2-T3 | Reviews spanning 8 distinct topics | Merged into ≤ 5 themes; no theme overflow | ⬜ PENDING |
| P2-T4 | < 5 reviews total | Analysis completes; themes may be < 5 | ⬜ PENDING |
| P2-T5 | Quotes contain username ("John said...") | PII stripped; quote anonymized | ⬜ PENDING |
| P2-T6 | Quotes contain email address | Email removed before storage | ⬜ PENDING |
| P2-T7 | LLM returns malformed JSON | Retry triggered; error logged; fallback applied | ⬜ PENDING |
| P2-T8 | Run same input twice | Themes are semantically consistent (not random) | ⬜ PENDING |

Run command:
```
py -m pytest tests/test_analyzer.py -v
```

---

## Exit Criteria

- [ ] All 8 test cases pass
- [ ] Theme count never exceeds 5 in any test run
- [ ] Zero PII in quote output (verified by automated PII scan)
- [ ] Token usage per run logged and within acceptable budget
- [ ] Prompt templates versioned and stored in `prompts/`

---

## Phase 2 Exit Status: **PENDING**
