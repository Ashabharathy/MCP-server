# Phase 5 Evaluation — Agent Orchestration & Full Pipeline

**Phase:** 5 — Agent Orchestration & Full Pipeline
**Status:** ⬜ PENDING
**Exit Criteria:** All tests below must pass before Phase 6 begins.

---

## Evaluation Summary

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| P5-T1 | Full pipeline run on sample data | All 5 stages succeed, run log written | ⬜ PENDING |
| P5-T2 | Dry-run mode produces no Google artifacts | No Doc created, no Gmail draft, pulse written locally | ⬜ PENDING |
| P5-T3 | Ingestion failure halts pipeline | Run exits non-zero, no analysis or delivery attempted | ⬜ PENDING |
| P5-T4 | Docs delivery failure marks run as partial | Gmail delivery still attempted, run log shows `"partial"` | ⬜ PENDING |
| P5-T5 | LLM retry on analyze stage | Simulated LLM failure retries 3x, then halts with error logged | ⬜ PENDING |
| P5-T6 | CLI flags override config file | `--weeks 12` overrides config `weeks: 8`, correct date range used | ⬜ PENDING |
| P5-T7 | Run log is written on partial failure | Run log exists with `overall_status: "partial"` and `errors` list | ⬜ PENDING |
| P5-T8 | Stage durations captured in run log | Each stage has a `duration_seconds` field in the log | ⬜ PENDING |

---

## Detailed Test Cases

### P5-T1 — Full Pipeline Run (Happy Path)

**Goal:** Confirm all 5 stages run successfully from CLI invocation to Google Doc URL and Gmail draft.

**Setup:**
- Valid sample CSVs in `ingestion/sample_data/`
- Phase 4 MCP servers running and configured
- `config/agent-config.json` populated

**Steps:**
1. Run: `python agent.py --config config/agent-config.json`
2. Observe console output
3. Check `runs/` directory for run log
4. Verify Google Doc created
5. Verify Gmail draft created

**Expected:**
- Console shows each stage completing successfully
- `runs/run_<uuid>.json` written with `overall_status: "success"`
- Google Doc URL in run log
- Gmail Drafts folder contains draft with correct subject
- Exit code 0

**Exit:** ⬜ PENDING

---

### P5-T2 — Dry-Run Mode

**Goal:** Confirm dry-run produces pulse files locally but creates no Google artifacts.

**Steps:**
1. Run: `python agent.py --config config/agent-config.json --dry-run`
2. Check `runs/` directory
3. Check Google Drive and Gmail Drafts

**Expected:**
- `runs/pulse_<date>.md` and `runs/pulse_<date>.txt` created locally
- `runs/run_<uuid>.json` has `run_mode: "dry-run"`
- No new Google Doc in Drive
- No new Gmail draft
- Exit code 0

**Exit:** ⬜ PENDING

---

### P5-T3 — Ingestion Failure Halts Pipeline

**Goal:** Confirm a missing CSV causes the run to halt before any LLM calls are made.

**Steps:**
1. Run with a non-existent CSV path: `python agent.py --appstore-csv /nonexistent.csv`
2. Observe behavior

**Expected:**
- Error logged: `"ingestion failed: file not found"`
- No analyze, generate, or delivery stages are invoked
- No run log written to `runs/` (or a minimal failure log only)
- Exit code non-zero (e.g., 1)

**Exit:** ⬜ PENDING

---

### P5-T4 — Docs MCP Failure Marks Run Partial, Gmail Still Runs

**Goal:** Confirm that a Docs delivery failure does not skip Gmail delivery.

**Setup:**
- Docs MCP server blocked/stopped
- Gmail MCP server running normally

**Steps:**
1. Run full pipeline with Docs MCP unavailable
2. Observe stage logs

**Expected:**
- `delivery_docs.status: "partial"` in run log
- `delivery_gmail.status: "success"` in run log
- Gmail draft created successfully
- `overall_status: "partial"` in run log
- Exit code non-zero

**Exit:** ⬜ PENDING

---

### P5-T5 — LLM Retry on Analyze Stage

**Goal:** Confirm that LLM failures trigger retries with exponential back-off before halting.

**Setup:**
- Mock or intercept LLM calls to return errors for 3 consecutive calls

**Steps:**
1. Run pipeline with mocked LLM returning errors
2. Observe retry behavior and final exit

**Expected:**
- 3 retry attempts logged with back-off delays
- After 3rd failure, run halts with error: `"analyze failed after 3 retries"`
- No generate or delivery stages invoked
- Exit code non-zero

**Exit:** ⬜ PENDING

---

### P5-T6 — CLI Flags Override Config File

**Goal:** Confirm runtime CLI flags take precedence over values in `agent-config.json`.

**Setup:**
- `agent-config.json` has `"weeks": 8`

**Steps:**
1. Run: `python agent.py --config config/agent-config.json --weeks 12`
2. Inspect run log `date_range`

**Expected:**
- `date_range.from` in run log is approximately 12 weeks before today (not 8)
- Ingestion uses 12-week window

**Exit:** ⬜ PENDING

---

### P5-T7 — Run Log Written on Partial Failure

**Goal:** Confirm a run log is always written, even on partial failure.

**Steps:**
1. Run pipeline with Docs MCP unavailable (same as P5-T4)
2. Check `runs/` directory after run

**Expected:**
- `runs/run_<uuid>.json` exists
- Contains `overall_status: "partial"`
- `errors` list contains at least one entry
- All stages that ran have their duration recorded

**Exit:** ⬜ PENDING

---

### P5-T8 — Stage Durations in Run Log

**Goal:** Confirm every stage records its duration in the run log.

**Steps:**
1. Run full pipeline (success or partial)
2. Open run log

**Expected:**
- Each of `ingestion`, `analysis`, `generation`, `delivery_docs`, `delivery_gmail` has `duration_seconds` key
- `total_duration_seconds` matches sum of stage durations (within rounding margin)

**Exit:** ⬜ PENDING

---

## Phase 5 Exit Gate

| Gate | Condition | Status |
|------|-----------|--------|
| Happy path | P5-T1 passes | ⬜ |
| Dry-run safe | P5-T2 passes | ⬜ |
| Fault tolerance | P5-T3, P5-T4, P5-T5 pass | ⬜ |
| Config handling | P5-T6 passes | ⬜ |
| Observability | P5-T7, P5-T8 pass | ⬜ |

**Phase 5 Exit Status: ⬜ PENDING — Begin Phase 6 only after all gates are green.**
