# Phase 3 — Evaluation & Exit Criteria

## Test Scope
- Word count enforcement
- Structure and scannability
- PII absence
- Output consistency

---

## Test Cases

| ID | Test Case | Expected Result | Status |
|---|---|---|---|
| P3-T1 | Generate pulse from 3 themes | Output contains top 3 themes, 3 quotes, 3 action ideas | ⬜ PENDING |
| P3-T2 | Word count check | Output ≤ 250 words | ⬜ PENDING |
| P3-T3 | LLM returns > 250 words | Truncation or retry triggered; final output ≤ 250 words | ⬜ PENDING |
| P3-T4 | PII scan on generated pulse | Zero PII detected | ⬜ PENDING |
| P3-T5 | Structure check | Pulse has headers/bullets; is scannable | ⬜ PENDING |
| P3-T6 | Markdown output | Valid markdown rendered correctly | ⬜ PENDING |
| P3-T7 | Run 5 times on same input | Outputs are semantically consistent (low hallucination variance) | ⬜ PENDING |
| P3-T8 | Themes input with only 1 theme | Pulse generates gracefully with available data | ⬜ PENDING |

Run command:
```
py -m pytest tests/test_generator.py -v
```

---

## Exit Criteria

- [ ] All 8 test cases pass
- [ ] 100% of runs produce output ≤ 250 words
- [ ] Zero PII in any generated pulse (5-run sample audit)
- [ ] Output validated as scannable by a human reviewer
- [ ] Markdown and plain text variants both generated correctly

---

## Phase 3 Exit Status: **PENDING**
