# Phase 6 Plan — Hardening & Production Readiness

**Phase:** 6 — Hardening & Production Readiness
**Status:** ⬜ PENDING
**Depends on:** Phase 5 complete and all exit gates green
**Reference:** `Docs/implementation-plan.md` § Phase 6

---

## Goal

Audit the system for security and privacy compliance, add observability and failure alerting, validate resilience under edge cases, and confirm that every constraint from `problemstatement.md` is met. The agent should be operable by a new team member without prior context.

---

## Context & Rationale

A working pipeline is not the same as a production-ready one. Phase 6 systematically closes the gaps:

- **Security:** The pipeline handles user-generated content that may contain PII, and it accesses Google Workspace via OAuth. Both are attack surfaces that need explicit validation.
- **Observability:** Without structured alerts and logs, failures are invisible until someone notices a missing weekly pulse.
- **Resilience:** Edge cases like zero reviews, malformed CSVs, and oversized review volumes must be explicitly tested — not left as assumptions.
- **Maintainability:** The system must be operable by someone who wasn't involved in building it. A runbook and final constraint audit are the acceptance tests for this.

---

## What We Are Building

### 1. Automated Security Audit

An automated scan (`scripts/security_audit.py`) that checks the entire repository for:

**Credential patterns:**
```
client_secret, client_id, access_token, refresh_token,
GOOGLE_API_KEY, AIza[a-zA-Z0-9_]{35}, ya29\.[a-zA-Z0-9_-]+,
Bearer [a-zA-Z0-9._-]+, private_key
```

**PII in log files:**
- Scan all files in `runs/` for email addresses, phone numbers, and names from sample data
- Confirm zero matches

**Gitignore audit:**
- Confirm `config/mcp-config-*.json` (real, non-template files) are in `.gitignore`
- Confirm `runs/` is in `.gitignore` (run logs are local artifacts, not committed)
- Confirm `ingestion/output/` is in `.gitignore`

**Pass criteria:** Zero findings across all checks.

---

### 2. Input Validation Hardening

Tighten the ingestion layer to reject or truncate problematic inputs gracefully:

| Scenario | Behavior |
|----------|---------|
| Rating outside 1–5 range | Skip review, log warning |
| Review text > 2000 characters | Truncate to 2000 chars, log warning |
| Date before 2015 or in the future | Skip review, log warning |
| CSV encoding error | Skip row, log warning with row number |
| Entire CSV is empty (header only) | Return empty list, log info |
| All reviews filtered out by date | Return empty list, halt pipeline with clear error |

These cases are verified by dedicated tests in Phase 6 eval.

---

### 3. Token Budget Guardrail

A configurable per-run token budget is enforced across the analyze and generate stages:

```json
"analysis": {
  "token_budget": 50000
}
```

**Behavior:**
- Token usage is tracked cumulatively across both stages
- If cumulative usage exceeds `token_budget` before generation completes, the run halts with: `"token budget exceeded: used X of Y tokens"`
- This is logged to the run log under `errors`
- Alert is dispatched (see Alerting below)

This prevents runaway costs from unusually large review volumes.

---

### 4. Failure Alerting

On any unrecoverable failure (ingestion halt, all LLM retries exhausted, token budget exceeded), an alert is dispatched through a configurable channel.

**Alert config:**
```json
"alerting": {
  "channel": "gmail",            // "gmail" | "slack" | "none"
  "recipient": "admin@example.com",
  "slack_webhook_url": null      // only needed if channel = "slack"
}
```

**Alert content:**
- `run_id`
- Stage where failure occurred
- Error summary (one line)
- Link to run log file (local path)

**Gmail channel:** Uses Gmail MCP `draft_email` tool (does not auto-send — creates a draft for the configured recipient). If the Gmail MCP is itself unavailable, the alert is written to a local `runs/alerts.log` file as a fallback.

**Slack channel:** HTTP POST to `slack_webhook_url`. No library dependency — uses Python `urllib` only.

---

### 5. Edge Case Validation

Explicit tests for production edge cases (defined in Phase 6 eval):

| Edge Case | Expected Behavior |
|-----------|------------------|
| Zero reviews after date filter | Pipeline halts at ingestion with clear message |
| All reviews are 1-star (no positive signal) | Themes and pulse generated normally; no crash |
| Review count very large (1000+) | Chunked batching in analyzer; token budget respected |
| LLM returns > 5 themes | Post-processor merges smallest until ≤ 5; no crash |
| Pulse word count cannot be reduced below 250 after 2 retries | Hard truncation applied; `truncated: true` in run log |
| MCP server returns malformed JSON response | Delivery marked partial; error logged; no crash |

---

### 6. Final Constraint Audit

A structured checklist cross-referencing every constraint in `problemstatement.md`:

| Constraint | Verification Method | Status |
|------------|-------------------|--------|
| Public CSV exports only — no scraping | Code review: ingestion module has no HTTP client or auth | ⬜ |
| Maximum 5 themes | Unit test: post-processor enforced; prompt reviewed | ⬜ |
| Pulse ≤ 250 words | Unit test: word count check + truncation test | ⬜ |
| No PII in any output artifact | Security audit scan on run logs + generated pulse | ⬜ |
| All Google Workspace via MCP servers only | Code review: delivery module has no direct Google REST calls | ⬜ |
| No credentials in agent codebase | Security audit script — zero findings | ⬜ |

---

### 7. Runbook

A runbook (`Docs/runbook.md`) written for a new operator. Must be walkthrough-tested — a team member unfamiliar with the project reads it cold and runs the agent successfully.

**Runbook sections:**
1. Prerequisites (Python version, dependencies, MCP server requirements)
2. One-time setup (Google Cloud Console, MCP server configuration, config file setup)
3. Running the agent manually (full run, dry-run, with CLI flags)
4. Interpreting run logs (what each field means, how to identify partial failures)
5. Common failure modes and resolutions:
   - MCP server not running
   - CSV export file in wrong format or location
   - LLM rate limit or token budget exceeded
   - No reviews in the date window
6. Scheduling setup (cron example)

---

## Key Decisions at This Phase

| Decision | Choice | Reason |
|----------|--------|--------|
| Alert channel | Configurable (gmail/slack/none) | Avoids hardcoding operational preferences; operators choose their channel |
| Token budget | Configurable per-run | Adapts to different review volumes and cost targets |
| Runbook acceptance test | Walkthrough by new team member | Documentation that can't be followed is not documentation |
| Gitignore for run logs | Yes — `runs/` excluded | Run logs contain operational data not suitable for version control |

---

## Folder Structure Added in Phase 6

```
MCP/
├── scripts/
│   └── security_audit.py       # Automated credential + PII scan
├── .gitignore                   # Updated with runs/, ingestion/output/, real MCP configs
├── Docs/
│   └── runbook.md              # Operator runbook (written and walkthrough-tested)
└── tests/
    └── test_hardening.py       # Edge case + security tests
```

---

## Deliverables

- [ ] `scripts/security_audit.py` — automated scan, zero findings required
- [ ] `.gitignore` — all runtime artifacts excluded
- [ ] Token budget guardrail implemented and tested
- [ ] Failure alerting implemented (Gmail or Slack channel)
- [ ] All 6 edge case scenarios tested and passing
- [ ] Final constraint audit checklist signed off (all 6 constraints confirmed)
- [ ] `Docs/runbook.md` written and walkthrough-tested
- [ ] `tests/test_hardening.py` all tests green

---

## Phase 6 Exit Gate

All deliverables above checked off, and all Phase 6 eval tests pass.
See `Docs/phases/phase6/eval.md` for test cases.

**Phase 6 completion = project production-ready.**
