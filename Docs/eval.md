# Evaluation & Exit Criteria — GROWW Weekly Review Pulse Agent

## Purpose

This document defines the testing approach, acceptance tests, and **exit criteria** for each implementation phase. A phase is considered complete only when all exit criteria are met.

---

## Phase 1 — Review Ingestion

### Test Scope
- Parser correctness for App Store and Play Store CSV formats
- Date-range filtering
- Schema normalization and data quality

### Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| P1-T1 | Parse valid App Store CSV export | All records normalized to `{ id, rating, title, text, date, source }` |
| P1-T2 | Parse valid Play Store CSV export | All records normalized correctly |
| P1-T3 | Apply 8-week date filter | Only reviews within last 8 weeks returned |
| P1-T4 | Apply 12-week date filter | Only reviews within last 12 weeks returned |
| P1-T5 | Duplicate reviews in input | Deduplication removes duplicates; unique set returned |
| P1-T6 | Missing fields in CSV row | Row skipped or defaulted gracefully; no crash |
| P1-T7 | Non-UTF-8 encoded characters | Handled without crash; characters sanitized |
| P1-T8 | Empty CSV file | Returns empty list; no crash |
| P1-T9 | 0 reviews in date range | Returns empty list; pipeline handles gracefully |

### Exit Criteria
- [ ] All 9 test cases pass
- [ ] Parser handles both CSV formats without manual intervention
- [ ] No PII fields in normalized output (verified by field audit)
- [ ] Code reviewed and merged

---

## Phase 2 — Theme Analysis

### Test Scope
- LLM clustering accuracy
- Theme count enforcement (≤ 5)
- Quote extraction quality
- PII removal from quotes

### Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| P2-T1 | 50 mixed reviews across 5 topics | ≤ 5 themes returned, each theme labelled |
| P2-T2 | 10 reviews all about KYC | 1 theme returned (not inflated to 5) |
| P2-T3 | Reviews spanning 8 distinct topics | Merged into ≤ 5 themes; no theme overflow |
| P2-T4 | < 5 reviews total | Analysis completes; themes may be < 5 |
| P2-T5 | Quotes contain username ("John said...") | PII stripped; quote anonymized |
| P2-T6 | Quotes contain email address | Email removed before storage |
| P2-T7 | LLM returns malformed JSON | Retry triggered; error logged; fallback applied |
| P2-T8 | Run same input twice | Themes are semantically consistent (not random) |

### Exit Criteria
- [ ] All 8 test cases pass
- [ ] Theme count never exceeds 5 in any test run
- [ ] Zero PII in quote output (verified by automated PII scan)
- [ ] Token usage per run logged and within acceptable budget
- [ ] Prompt templates versioned and stored in `prompts/`

---

## Phase 3 — Pulse Generation

### Test Scope
- Word count enforcement
- Structure and scannability
- PII absence
- Output consistency

### Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| P3-T1 | Generate pulse from 3 themes | Output contains top 3 themes, 3 quotes, 3 action ideas |
| P3-T2 | Word count check | Output ≤ 250 words |
| P3-T3 | LLM returns > 250 words | Truncation or retry triggered; final output ≤ 250 words |
| P3-T4 | PII scan on generated pulse | Zero PII detected |
| P3-T5 | Structure check | Pulse has headers/bullets; is scannable |
| P3-T6 | Markdown output | Valid markdown rendered correctly |
| P3-T7 | Run 5 times on same input | Outputs are semantically consistent (low hallucination variance) |
| P3-T8 | Themes input with only 1 theme | Pulse generates gracefully with available data |

### Exit Criteria
- [ ] All 8 test cases pass
- [ ] 100% of runs produce output ≤ 250 words
- [ ] Zero PII in any generated pulse (5-run sample audit)
- [ ] Output validated as scannable by a human reviewer
- [ ] Markdown and plain text variants both generated correctly

---

## Phase 4 — MCP Server Setup & Integration

### Test Scope
- MCP server connectivity and tool call success
- Google Docs creation and update via MCP
- Gmail draft creation via MCP
- Auth isolation (no credentials in app code)

### Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| P4-T1 | MCP server starts without error | Server running; tool list returned |
| P4-T2 | Call `create_document` with sample pulse | New Google Doc created; URL returned |
| P4-T3 | Call `update_document` on existing doc | Doc content updated; no duplicate doc created |
| P4-T4 | Call `draft_email` with pulse content | Draft email appears in Gmail Drafts |
| P4-T5 | Scan app codebase for credentials | Zero API keys / OAuth tokens found in app code |
| P4-T6 | MCP server config missing | Clear error raised; app does not crash silently |
| P4-T7 | Google Docs MCP unavailable | Error caught; delivery skipped; run logged as partial |
| P4-T8 | Gmail MCP unavailable | Error caught; delivery skipped; run logged as partial |

### Exit Criteria
- [ ] All 8 test cases pass
- [ ] Confirmed zero credentials in application source code (automated scan)
- [ ] MCP config template documented without real secrets
- [ ] At least one successful e2e delivery: pulse → Google Doc + Gmail draft

---

## Phase 5 — Agent Orchestration & Full Pipeline

### Test Scope
- End-to-end pipeline correctness
- Error handling and retry behavior
- Scheduling and dry-run mode
- Logging completeness

### Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| P5-T1 | Full pipeline run with sample data | Pulse delivered to Google Doc + Gmail draft |
| P5-T2 | Dry-run mode | Pulse generated; no Google Doc created; no email drafted |
| P5-T3 | Ingestion fails (bad file) | Error logged; pipeline stops at ingestion; no partial delivery |
| P5-T4 | LLM call fails (timeout) | Retry 3x; error logged; alert triggered after final failure |
| P5-T5 | MCP delivery fails | Error logged; partial run marked; alert triggered |
| P5-T6 | Run log captured | Log contains: run ID, phase timings, token counts, delivery status |
| P5-T7 | Scheduled run (simulated) | Pipeline runs at configured time without manual trigger |
| P5-T8 | Configurable date range | Agent respects `--weeks 8` and `--weeks 12` flags |

### Exit Criteria
- [ ] All 8 test cases pass
- [ ] Full e2e run completes in < 3 minutes on sample dataset
- [ ] Dry-run mode verified to produce zero side effects
- [ ] Logs verified complete and machine-parseable
- [ ] Scheduler integration tested at least once

---

## Phase 6 — Hardening & Production Readiness

### Test Scope
- Security and privacy compliance
- Reliability under edge cases
- Observability and alerting

### Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| P6-T1 | Security scan: credentials in source | Zero findings |
| P6-T2 | Security scan: PII in logs | Zero PII in any log output |
| P6-T3 | Input with all-empty review texts | Pipeline handles gracefully; empty pulse generated |
| P6-T4 | LLM token budget exceeded | Run halted; budget warning logged |
| P6-T5 | Failure alert delivery | Alert sent (email / Slack) on pipeline failure |
| P6-T6 | Final constraint audit vs problemstatement.md | All 5 constraints satisfied and documented |
| P6-T7 | Runbook walkthrough | New team member can run pipeline using runbook alone |

### Exit Criteria
- [ ] All 7 test cases pass
- [ ] Security audit sign-off (no credentials, no PII in logs)
- [ ] All constraints from `problemstatement.md` verified in production config
- [ ] Runbook reviewed and approved
- [ ] Project considered production-ready

---

## Overall Completion Checklist

- [ ] Phase 1 exit criteria met
- [ ] Phase 2 exit criteria met
- [ ] Phase 3 exit criteria met
- [ ] Phase 4 exit criteria met
- [ ] Phase 5 exit criteria met
- [ ] Phase 6 exit criteria met
- [ ] Final e2e demo run recorded or witnessed
