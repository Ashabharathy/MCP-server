# Phase 6 Evaluation — Hardening & Production Readiness

**Phase:** 6 — Hardening & Production Readiness
**Status:** ⬜ PENDING
**Exit Criteria:** All tests below must pass. This is the final phase — passing all gates means the system is production-ready.

---

## Evaluation Summary

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| P6-T1 | Security audit — zero credentials in codebase | Automated scan returns zero findings | ⬜ PENDING |
| P6-T2 | Security audit — zero PII in run logs | Log scan returns zero PII matches | ⬜ PENDING |
| P6-T3 | Token budget exceeded halts run gracefully | Run halts with budget error, alert dispatched | ⬜ PENDING |
| P6-T4 | Edge case: zero reviews after date filter | Pipeline halts at ingestion with clear error message | ⬜ PENDING |
| P6-T5 | Edge case: all 1-star reviews | Themes and pulse generated normally, no crash | ⬜ PENDING |
| P6-T6 | Edge case: LLM returns 6 themes | Post-processor merges to ≤ 5, no crash | ⬜ PENDING |
| P6-T7 | Final constraint audit | All 6 constraints from problemstatement.md confirmed | ⬜ PENDING |

---

## Detailed Test Cases

### P6-T1 — Security Audit: Zero Credentials in Codebase

**Goal:** Confirm no API keys, OAuth tokens, or client secrets appear in any tracked file.

**Tool:** `scripts/security_audit.py`

**Scan patterns:**
```
client_secret, client_id, access_token, refresh_token,
GOOGLE_API_KEY, AIza[a-zA-Z0-9_]{35}, ya29\.[a-zA-Z0-9_-]+,
Bearer [a-zA-Z0-9._-]+, private_key
```

**Steps:**
1. Run: `python scripts/security_audit.py`
2. Review output

**Expected:**
- Output: `"Security audit PASSED: 0 findings"`
- `config/mcp-config-template.json` contains only `<PLACEHOLDER>` strings
- No real credentials in any `.py`, `.json`, `.txt`, or `.env` file tracked by git

**Exit:** ⬜ PENDING

---

### P6-T2 — Security Audit: Zero PII in Run Logs

**Goal:** Confirm no PII from reviews appears in any run log or generated pulse file.

**Steps:**
1. Run the full pipeline on sample data
2. Run PII scan on all files in `runs/`:
   - Regex patterns: email addresses, phone numbers, common Indian names from sample data

**Expected:**
- Zero email address matches in `runs/`
- Zero phone number matches in `runs/`
- Generated pulse quotes contain no names or locations
- Output: `"PII audit PASSED: 0 findings in runs/"`

**Exit:** ⬜ PENDING

---

### P6-T3 — Token Budget Exceeded Halts Run

**Goal:** Confirm the token budget guardrail stops the run before delivery and dispatches an alert.

**Setup:**
- Set `token_budget: 100` in `agent-config.json` (artificially low to trigger the budget)
- Alert channel set to `"gmail"` or `"none"` for testing

**Steps:**
1. Run full pipeline with a very low `token_budget`
2. Observe behavior after the analyze stage begins consuming tokens

**Expected:**
- Run halts mid-pipeline with error: `"token budget exceeded: used X of 100 tokens"`
- Run log has `overall_status: "partial"` and `errors` includes the budget message
- Alert is dispatched (or written to `runs/alerts.log` if channel is `"none"`)
- No delivery to Google Doc or Gmail (delivery stages not reached)

**Exit:** ⬜ PENDING

---

### P6-T4 — Edge Case: Zero Reviews After Date Filter

**Goal:** Confirm the pipeline halts cleanly when no reviews fall within the configured date window.

**Setup:**
- Use a reference date far in the future so all sample reviews are outside the window
- Or configure `weeks: 1` with stale export files

**Steps:**
1. Run pipeline with `reference_date` or export files such that zero reviews match the window
2. Observe behavior

**Expected:**
- Error logged: `"ingestion returned 0 reviews — pipeline halted"`
- No analyze, generate, or delivery stages invoked
- Exit code non-zero
- Minimal run log or no run log written

**Exit:** ⬜ PENDING

---

### P6-T5 — Edge Case: All 1-Star Reviews

**Goal:** Confirm the pipeline does not crash or produce malformed output when all reviews are 1-star.

**Setup:**
- Modify sample CSV so all 30 reviews have `rating = 1`

**Steps:**
1. Run full pipeline (dry-run is fine)
2. Inspect generated pulse

**Expected:**
- Pipeline completes all stages without error
- Pulse is generated with themes reflecting negative sentiment
- Pulse word count ≤ 250
- No crash or unhandled exception

**Exit:** ⬜ PENDING

---

### P6-T6 — Edge Case: LLM Returns More Than 5 Themes

**Goal:** Confirm the analyzer post-processor enforces the 5-theme limit regardless of LLM output.

**Setup:**
- Mock the LLM response to return 7 themes with different review counts

**Steps:**
1. Run the analyzer with a mocked LLM response containing 7 themes
2. Inspect the analyzer output

**Expected:**
- Analyzer output contains exactly 5 themes (smallest 2 merged into the nearest thematic neighbor or dropped)
- No crash or assertion error
- Log message: `"LLM returned 7 themes — merged to 5"`

**Exit:** ⬜ PENDING

---

### P6-T7 — Final Constraint Audit

**Goal:** Confirm every hard constraint from `problemstatement.md` is met by the implemented system.

**Method:** Combined code review + automated test evidence.

| Constraint | Verification | Pass Criteria | Status |
|------------|-------------|---------------|--------|
| Public CSV exports only — no scraping | Code review: no HTTP client in `ingestion/` | Zero network calls in ingestion module | ⬜ |
| Maximum 5 themes | Unit test: P2-T3 (theme cap) | Post-processor enforces cap, confirmed by P6-T6 | ⬜ |
| Pulse ≤ 250 words | Unit test: P3-T1, P3-T2 (word count + truncation) | Retry-truncate logic tested and green | ⬜ |
| No PII in any output artifact | P6-T2 (PII audit) | Zero PII findings in run logs | ⬜ |
| All Google Workspace via MCP only | Code review: `delivery/` module has zero direct Google API calls | No `google-api-python-client` import anywhere in delivery | ⬜ |
| No credentials in agent codebase | P6-T1 (security audit) | Zero credential findings | ⬜ |

**All 6 rows must be ⬜ → ✅ before this test passes.**

**Exit:** ⬜ PENDING

---

## Phase 6 Exit Gate

| Gate | Condition | Status |
|------|-----------|--------|
| Security clean | P6-T1 and P6-T2 pass | ⬜ |
| Guardrails working | P6-T3 passes | ⬜ |
| Edge cases handled | P6-T4, P6-T5, P6-T6 pass | ⬜ |
| All constraints confirmed | P6-T7 passes (all 6 rows green) | ⬜ |
| Runbook walkthrough-tested | New team member runs agent successfully using runbook alone | ⬜ |

**Phase 6 Exit Status: ⬜ PENDING**

**When all gates are green — the GROWW Weekly Review Pulse Agent is production-ready.**
