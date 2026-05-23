# Phase 5 Plan — Agent Orchestration & Full Pipeline

**Phase:** 5 — Agent Orchestration & Full Pipeline
**Status:** ⬜ PENDING
**Depends on:** Phase 1, 2, 3, 4 complete and all exit gates green
**Reference:** `Docs/implementation-plan.md` § Phase 5

---

## Goal

Connect all four pipeline stages into a single, reliable orchestrated agent that runs end-to-end: from review export to Google Doc creation and Gmail draft. Add configurable parameters, robust error handling, structured run logging, and a dry-run mode.

---

## Context & Rationale

Phases 1–4 produce four isolated, verified components. Phase 5 is the integration layer — it sequences them, manages state passing between stages, handles partial failures, and produces a structured run log that makes every run auditable.

Key design principles carried into this phase:
- **Halt on ingestion failure:** If no valid reviews are found, the run stops immediately. Delivering an empty pulse is worse than not delivering.
- **Partial delivery is allowed:** If a Docs or Gmail MCP call fails after retries, the run is marked partial and the pulse is saved locally. The pipeline does not crash.
- **Dry-run is first-class:** Any change to generation logic can be tested without creating Google artifacts.
- **No global state between stages:** Each stage receives the output of the previous one as an explicit argument. No shared globals, no implicit state.

---

## What We Are Building

### 1. Orchestrator (`agent.py`)

The main entry point sequences the pipeline in a fixed order:

```
ingest → analyze → generate → deliver(docs) → deliver(gmail) → log
```

Each stage function receives a typed input and returns a typed output. The orchestrator passes the output of each stage directly as the input of the next. If a stage raises a fatal error, the orchestrator catches it, logs it, and halts (or marks partial, depending on stage).

**Stage error behavior:**

| Stage | Error type | Behavior |
|-------|-----------|---------|
| Ingestion | No reviews found | Halt, log error, exit non-zero |
| Ingestion | File not found / parse error | Halt, log error, exit non-zero |
| Analyze | LLM call fails | Retry up to 3x with back-off; halt if all fail |
| Generate | LLM exceeds word limit | Retry up to 2x; truncate if still over |
| Generate | LLM call fails | Retry up to 3x with back-off; halt if all fail |
| Deliver (Docs) | MCP unavailable | Retry 2x; mark partial, continue to Gmail |
| Deliver (Gmail) | MCP unavailable | Retry 2x; mark partial, log |

---

### 2. CLI Interface

The agent is invoked from the command line with configurable flags:

```
python agent.py \
  --appstore-csv path/to/appstore.csv \
  --playstore-csv path/to/playstore.csv \
  --weeks 8 \
  --doc-id <existing_google_doc_id>   # optional; creates new doc if omitted \
  --recipient team@example.com \
  --model gpt-4o \
  --dry-run                           # optional; skips delivery \
  --output-dir ./runs/                # local output dir for logs and pulse \
  --log-level INFO
```

All flags also have equivalents in a JSON config file (`config/agent-config.json`), with CLI flags taking precedence over config file values.

---

### 3. Run Configuration Schema

`config/agent-config.json`:

```json
{
  "ingestion": {
    "appstore_csv": "ingestion/sample_data/appstore_sample.csv",
    "playstore_csv": "ingestion/sample_data/playstore_sample.csv",
    "weeks": 8
  },
  "analysis": {
    "model": "gpt-4o",
    "max_themes": 5,
    "token_budget": 50000
  },
  "generation": {
    "model": "gpt-4o",
    "max_words": 250,
    "max_retries": 2
  },
  "delivery": {
    "doc_id": null,
    "recipient": "team@example.com",
    "dry_run": false
  },
  "output_dir": "./runs/"
}
```

---

### 4. Structured Run Log

Every run writes a `run_<uuid>.json` file to `output_dir`:

```json
{
  "run_id": "f3a2b1...",
  "run_mode": "full",
  "started_at": "2025-03-10T09:00:00Z",
  "date_range": { "from": "2025-01-13", "to": "2025-03-10" },
  "stages": {
    "ingestion": {
      "status": "success",
      "review_count": 30,
      "duration_seconds": 0.4
    },
    "analysis": {
      "status": "success",
      "theme_count": 4,
      "tokens_used": 4200,
      "duration_seconds": 6.1
    },
    "generation": {
      "status": "success",
      "pulse_word_count": 238,
      "retries": 0,
      "tokens_used": 1100,
      "duration_seconds": 4.3
    },
    "delivery_docs": {
      "status": "success",
      "doc_url": "https://docs.google.com/document/d/...",
      "duration_seconds": 1.2
    },
    "delivery_gmail": {
      "status": "partial",
      "error": "MCP connection timeout",
      "duration_seconds": 3.0
    }
  },
  "overall_status": "partial",
  "total_duration_seconds": 15.0,
  "errors": ["delivery_gmail: MCP connection timeout"]
}
```

---

### 5. Dry-Run Mode

When `--dry-run` is set:
- All stages through `generate` run normally
- Delivery stages are skipped entirely
- The pulse (markdown, plain text, JSON) is written to `output_dir/pulse_<date>.{md,txt,json}`
- Run log `run_mode` is set to `"dry-run"`
- Exit code is 0 if generation succeeds, non-zero if any earlier stage fails

---

### 6. Scheduling

The agent is designed to be triggered by an external scheduler. It is stateless between runs — it reads fresh review exports, generates a fresh pulse, and writes a fresh run log.

**Recommended schedule:** Weekly (Monday 09:00), triggered by cron or cloud scheduler.

Example cron:
```
0 9 * * 1 cd /path/to/agent && python agent.py --config config/agent-config.json
```

The agent does not manage its own schedule — scheduler is external by design.

---

## Key Decisions at This Phase

| Decision | Choice | Reason |
|----------|--------|--------|
| Stage error model | Halt on ingestion; partial allowed on delivery | Empty pulse is worse than no pulse; delivery failures should not discard generated content |
| Config source | JSON file + CLI override | Separation of environment config from runtime flags |
| Run state storage | Append-only JSON log per run | No database dependency; logs are human-readable and auditable |
| Dry-run scope | Skips delivery only | Validates the full content pipeline without Google side effects |
| Scheduling | External scheduler (cron/cloud) | Keeps agent code simple and stateless |

---

## Folder Structure Added in Phase 5

```
MCP/
├── agent.py                    # Main orchestrator (implemented)
├── config/
│   ├── agent-config.json       # Runtime config (created here)
│   └── mcp-config-template.json
├── runs/                       # Run output directory
│   ├── run_<uuid>.json         # Run log per run
│   └── pulse_<date>.md         # Generated pulse (dry-run or saved copy)
└── tests/
    └── test_agent.py           # Orchestration integration tests
```

---

## Deliverables

- [ ] `agent.py` fully implemented with stage sequencing, error handling, and run logging
- [ ] CLI entry point with all flags documented
- [ ] `config/agent-config.json` config file schema
- [ ] Structured run log written per run
- [ ] Dry-run mode verified: no Google artifacts created, pulse written locally
- [ ] Full end-to-end pipeline run on sample data with all stages green
- [ ] `tests/test_agent.py` with integration tests covering dry-run, partial failure, and full run scenarios

---

## Phase 5 Exit Gate

All deliverables above checked off, and all Phase 5 eval tests pass.
See `Docs/phases/phase5/eval.md` for test cases.
