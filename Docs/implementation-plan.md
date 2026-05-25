# Implementation Plan — GROWW Weekly Review Pulse Agent

## Overview

This plan describes how we build the GROWW Weekly Review Pulse agent in six sequential phases. Each phase has a clear goal, the decisions and reasoning behind our approach, and a well-defined set of deliverables. Coding specifics are handled in the codebase; this document captures *what* we are building in each phase and *why* we are building it that way.

Exit criteria for each phase are defined in `eval.md`.

---

## Phase 1 — Foundation & Review Ingestion

### Goal
Establish the project foundation and build a reliable, repeatable mechanism to load raw app store reviews and prepare them for AI analysis.

### Context & Rationale
The entire pipeline depends on having clean, normalized review data. App Store and Play Store exports use different field names, encodings, and date formats — so a dedicated normalization layer is essential before any analysis begins. We handle this as Phase 1 because every downstream component depends on its output.

We deliberately limit the ingestion source to **official CSV exports only** (from App Store Connect and Google Play Console). This is a hard constraint: no scraping, no third-party review aggregators, no login-based access. This keeps us legally compliant with Apple and Google's terms of service and ensures the data is stable and structured.

### What We Are Building

**Unified review schema:** Both store exports are mapped to a single normalized format — `{ id, rating, title, text, date, source }`. The `source` field distinguishes App Store vs Play Store records for downstream filtering if needed.

**Date-range filtering:** The agent is configurable to pull the last 8 or 12 weeks of reviews. This window is set in the agent's run configuration, not hardcoded. The default is 8 weeks.

**Data quality handling:** Reviews with missing text fields are excluded. Duplicate records (same review appearing in multiple exports or re-exported overlapping windows) are deduplicated by review ID or by a content fingerprint (date + title + text hash). Encoding is normalized to UTF-8.

**No PII at ingestion:** Reviewer usernames and user IDs — if present in export fields — are excluded from the normalized output at this layer. We do not need them for any downstream analysis.

### Key Decisions Made at This Phase
- Use official exports only, not scraping (constraint from `problemstatement.md` — see D-002)
- Normalize both sources into one schema rather than handling them separately throughout the pipeline
- Date range is configurable (not hardcoded) to support flexible re-runs

### Deliverables
- `ingestion/` module: parsers for both CSV formats, normalization logic, deduplication, date filtering
- Sample normalized dataset (using synthetic/anonymized reviews) for use in all subsequent phases
- Passing tests for all ingestion scenarios (see `eval.md` Phase 1)

---

## Phase 2 — Theme Analysis

### Goal
Use an LLM to semantically cluster the normalized reviews into a maximum of 5 meaningful themes, and extract clean, anonymized user quotes that represent each theme.

### Context & Rationale
The core analytical value of the agent is grouping hundreds of reviews into digestible themes so product and support teams can act on patterns rather than individual reviews. This is inherently a semantic task — keyword matching would miss paraphrased complaints, contextual issues, and cross-cutting themes.

We use an LLM for this clustering step because:
- It understands meaning and context, not just keywords
- It can be prompted to group flexibly based on what users are actually saying
- It can produce structured output (JSON) that is easy to process programmatically

The constraint of **maximum 5 themes** is enforced at two levels: in the prompt (the LLM is instructed to cluster into at most 5 groups) and in post-processing code (if the LLM returns 6+ themes, we merge the smallest ones until ≤ 5 remain). This dual enforcement is deliberate because LLMs are non-deterministic and can violate prompt instructions.

### What We Are Building

**LLM Provider:** Groq Llama-3.3-70b-versatile is used as the LLM provider for this phase. Rate limits: 30 requests/minute, 1K requests/day, 12K tokens/minute, 100K tokens/day.

**Dataset sampling:** To stay within Groq's token limits, we sample 500 reviews from the full dataset (stratified by rating to maintain the original distribution: ~20% 1-star, ~15% 2-star, ~15% 3-star, ~20% 4-star, ~28% 5-star).

**Batching strategy:** Reviews are processed in batches of 50 per LLM call (~5K tokens per batch). This results in 10 batches total for 500 reviews. Each batch is processed sequentially to stay within the 30 requests/minute and 1K requests/day limits. Total token usage: ~50K tokens (well within the 100K daily limit).

**Token budget management:** The analyzer logs token consumption per batch and halts if the cumulative token count approaches the 100K daily limit. Batches are designed to fit within the 12K tokens/minute limit with headroom.

**Prompt design for clustering:** The prompt instructs the LLM to read all review texts in the current batch, identify the most common complaint or feedback categories, and return a JSON structure with: theme name, list of review IDs in the theme, and 2–3 representative verbatim quotes per theme. The prompt explicitly states the 5-theme maximum.

**Structured output:** We use the LLM's JSON-mode or structured output capability to get a machine-parseable response. This avoids fragile text parsing and makes the post-processing deterministic.

**Post-processing enforcement:** After receiving the LLM response, we sort themes by review count (descending) and truncate or merge to ≤ 5. If the LLM returns fewer than 5, that is fine — we do not pad.

**PII stripping from quotes:** Before quotes leave this module, they go through two passes:
1. A regex pass that removes structured PII — email addresses, phone numbers, numeric IDs
2. An LLM pass that removes contextual PII — names, locations, phrases like "I, Ramesh from Delhi..."

This two-pass approach is chosen because regex is fast and reliable for structured patterns, but misses natural-language PII that only semantic understanding can detect.

**Token budget management:** We log the token count consumed per analyzer run and per batch. The system is designed to operate within Groq's 100K tokens/day limit by processing exactly 500 reviews in 10 batches of 50 reviews each (~50K total tokens). If review volumes grow beyond 500, the sampling strategy can be adjusted or the batch size reduced to stay within token limits.

### Key Decisions Made at This Phase
- Dual enforcement of ≤ 5 themes (prompt + code) — see D-003
- Two-pass PII stripping (regex + LLM) — see D-004
- LLM structured output (JSON mode) to avoid text parsing fragility
- Prompt templates are version-controlled in `prompts/` so changes are auditable

### Deliverables
- `analyzer/` module: LLM clustering call, theme post-processor, PII stripper
- `prompts/theme-analysis-v1.txt`: initial prompt template
- Structured theme output schema documented
- Token usage logged per run

---

## Phase 3 — Pulse Generation

### Goal
Transform the themed analysis into a polished, scannable weekly pulse note that is ≤ 250 words — suitable for leadership, product, and support teams to read in under two minutes.

### Context & Rationale
The weekly pulse is the primary deliverable of the entire system. It must be concise enough to be read quickly (≤ 250 words), structured enough to be scannable (headers, bullets), and grounded in real user language (actual quotes). An LLM is ideal for this generation task because it can write in a clear, professional style given structured inputs.

The 250-word limit is a hard constraint from the problem statement. LLMs often exceed word limits even when instructed, so we enforce this with a retry-then-truncate strategy: if the first generation exceeds 250 words, we re-prompt with a stricter instruction (max 2 retries). If still over, we truncate — preserving structure priority: themes first, then quotes, then action ideas.

### What We Are Building

**Pulse structure:** The generated pulse always contains three sections:
- **Top 3 Themes** — one-sentence summary per theme with review count context
- **User Voices** — 3 anonymized user quotes (one per top theme)
- **Action Ideas** — 3 specific, concrete improvement suggestions derived from the themes

**Prompt design for generation:** The prompt receives the top 3 themes (with summaries and quotes) and instructs the LLM to write a weekly pulse in the defined structure, staying within 250 words, using plain language accessible to non-technical stakeholders.

**Word count enforcement:** After generation, we count words. If over 250: retry with a stricter prompt noting the word count overage. If still over after 2 retries: truncate the output, preserving the section structure (cut from the bottom of the action ideas section first).

**Output variants:** The pulse is produced in three formats:
- **Markdown** — for Google Docs delivery (formatted with headers and bullets)
- **Plain text** — for Gmail email body (readable without markdown rendering)
- **Structured JSON** — for run logging and auditability

**Final PII check:** Before the pulse leaves this module, a final PII scan (same two-pass approach as Phase 2) is applied. This is a safety net — quotes were already sanitized in Phase 2, but the generation step could theoretically re-introduce PII from review context in the prompt.

### Key Decisions Made at This Phase
- Retry-then-truncate strategy for word count enforcement — see D-005
- Three output formats (markdown, plain text, JSON) to serve different downstream consumers
- Final PII pass as a safety net even though Phase 2 already stripped quotes

### Deliverables
- `generator/` module: pulse generation, word count validation, retry logic, output formatter
- `prompts/pulse-generation-v1.txt`: initial prompt template
- Pulse output schema documented

---

## Phase 4 — MCP Server Setup & Google Workspace Integration

### Goal
Set up and validate the Google Docs MCP server and Gmail MCP server, and integrate them into the agent as the exclusive delivery mechanism. Confirm that the agent never touches Google credentials directly.

### Context & Rationale
This is the most infrastructure-heavy phase. The decision to use MCP servers rather than direct Google REST API calls is a core architectural constraint of the project (see D-001). MCP servers act as a trust boundary: they hold the OAuth 2.0 credentials and expose clean tools (`create_document`, `draft_email`) that the agent calls without any knowledge of the underlying API.

The practical implication is that this phase requires one-time setup work outside the agent codebase — configuring OAuth consent in Google Cloud Console and setting up the MCP servers with credentials. Once done, the agent never needs to touch credentials again.

### What We Are Building

**Google Docs MCP Server setup:**
- Select and configure a Google Docs-compatible MCP server (`@modelcontextprotocol/server-gdrive` or equivalent)
- Create a Google Cloud project, enable the Google Docs API, configure an OAuth 2.0 consent screen and service credentials
- Store credentials in the MCP server's configuration (not in any file tracked by the agent repository)
- Validate the server exposes at minimum: `create_document`, `update_document`, `get_document_url`
- Test idempotency: calling `update_document` on an existing doc replaces content, does not create a duplicate

**Gmail MCP Server setup:**
- Select and configure a Gmail-compatible MCP server
- Configure OAuth 2.0 consent for Gmail send/draft scope
- Store credentials in MCP server config
- Validate the server exposes at minimum: `draft_email` (creates a draft without sending), `send_email`
- Default behavior: create a draft, not auto-send, to allow human review before dispatch

**Agent delivery module (`delivery/`):**
- Thin wrapper layer that the agent orchestrator calls
- Translates agent-level intents ("save pulse to Docs", "draft pulse email") into specific MCP tool calls
- Handles MCP server unavailability gracefully (error logged, run marked partial, no crash)

**MCP config template:**
- A `config/mcp-config-template.json` file documents the shape of MCP server configuration without any real credentials
- This is safe to commit and serves as the setup guide for new environments

**Credential audit:**
- An automated scan confirms that no API keys, OAuth tokens, or client secrets appear anywhere in the agent source code or config files tracked in the repository

### Key Decisions Made at This Phase
- MCP servers as the only Google Workspace integration path — see D-001
- Default to "draft" mode for Gmail (not auto-send) to allow human review
- MCP server credentials are managed outside the agent repo entirely
- Idempotent document updates (update existing weekly doc, not create a new one each re-run)

### Deliverables
- Running Google Docs MCP server (local or cloud-hosted)
- Running Gmail MCP server (local or cloud-hosted)
- `delivery/` module: MCP tool call wrappers for Docs and Gmail
- `config/mcp-config-template.json`
- Credential audit passing (zero credentials in agent codebase)
- At least one successful end-to-end delivery: pulse → Google Doc URL returned + Gmail draft created

---

## Phase 5 — Agent Orchestration & Full Pipeline

### Goal
Connect all pipeline stages into a single, reliable orchestrated agent that runs end-to-end: from review export to Google Doc and Gmail draft. Add scheduling, configurable parameters, error handling, and structured logging.

### Context & Rationale
Phases 1–4 produce isolated, working components. Phase 5 is about wiring them together into a coherent system that behaves predictably in production. The orchestrator is the agent's brain — it sequences the stages, manages state across them, handles failures gracefully, and produces a log that tells us exactly what happened in each run.

A key design choice here is **pipeline halt on ingestion failure**. If no valid reviews can be loaded, we stop immediately and do not deliver an empty or malformed pulse. Every other stage's failure is handled with retries and partial-run logging — but ingestion failure is a non-starter.

We also build **dry-run mode** as a first-class feature. This allows the pipeline to run completely — including full analysis and pulse generation — without creating a Google Doc or drafting an email. Dry-run is essential for testing changes and for auditing generated content before it goes live.

### What We Are Building

**Orchestrator sequencing:**
The agent runs stages in a fixed sequence with explicit handoffs:
```
ingest → analyze → generate → deliver (Docs) → deliver (Gmail) → log
```
Each stage receives the output of the previous stage as input. Stages do not share global state.

**Run configuration:**
All tunable parameters are externalized into a config file and/or CLI flags:
- `--weeks` : date range (8 or 12)
- `--dry-run` : skip delivery, output pulse to stdout/file only
- `--doc-id` : Google Doc ID to update (if omitted, creates a new doc)
- `--recipient` : email address for Gmail draft
- `--model` : LLM model override

**Error handling and retry strategy:**
- LLM call failures: retry up to 3 times with exponential back-off
- MCP tool call failures: retry up to 2 times; on final failure, mark delivery as partial and continue (do not halt the whole run)
- Ingestion failures: halt immediately, log the failure, alert if alerting is configured
- Partial runs are logged with a `status: "partial"` field so they are distinguishable from full successes

**Structured run log:**
Every run writes a JSON log entry containing:
- `run_id` (UUID)
- `run_mode` (full / dry-run)
- `date_range` (from / to)
- `review_count` (records ingested)
- `theme_count` (themes identified)
- `pulse_word_count`
- `llm_tokens_used` (per stage)
- `docs_delivery_status` (success / partial / skipped)
- `gmail_delivery_status` (success / partial / skipped)
- `doc_url` (if created)
- `duration_seconds` (per stage + total)
- `errors` (list, if any)

**Weekly scheduling:**
The orchestrator is designed to be triggered by an external scheduler (cron on a local machine, or a cloud scheduler job). The scheduler calls the agent with a fixed config. The agent is stateless between runs — it reads from the config and the review exports, writes its outputs, and exits.

### Key Decisions Made at This Phase
- Pipeline halts on ingestion failure, partial delivery is allowed on downstream failures
- Dry-run mode is a first-class feature, not an afterthought
- Run state is not stored in a database — each run is independent; the run log is append-only
- All config is externalized; no hardcoded parameters in agent code

### Deliverables
- `agent.py` (or equivalent): main orchestrator
- CLI entry point with all configurable flags
- Structured run log schema documented
- Dry-run mode verified with no side effects
- Full end-to-end pipeline run on sample data

---

## Phase 6 — Hardening & Production Readiness

### Goal
Audit the system for security and privacy compliance, add observability and alerting, validate resilience under edge cases, and ensure the system is maintainable by a new team member without guidance.

### Context & Rationale
Production readiness is not just about the happy path working. It means the system is safe (no credentials exposed, no PII leaking), observable (we know when something goes wrong before users do), and maintainable (anyone on the team can operate it). This phase systematically verifies all of that.

The security audit is particularly critical given that the pipeline processes user-generated content (reviews) that may contain PII, and interacts with Google Workspace accounts. We need confidence that PII stripping is effective and that credentials are fully isolated in MCP servers.

### What We Are Building

**Security audit:**
- Automated scan of all source files for credential patterns (API keys, OAuth tokens, client secrets)
- Manual review of log output across all phases to confirm zero PII appears in any log field
- Confirmation that the MCP server credential files are outside the agent repository and excluded from version control

**Input validation hardening:**
- All ingestion fields are validated against the expected schema with explicit type and format checks
- Reviews with malformed dates, out-of-range ratings, or excessively long text fields are filtered or truncated with warnings logged
- Edge cases tested: all reviews have empty text, all reviews are 1-star, review count is 0

**Token budget guardrails:**
- A configurable token budget per run is set in config
- If cumulative LLM token usage exceeds the budget mid-run, the run halts with a budget warning logged
- This prevents runaway costs from unusually large review volumes

**Failure alerting:**
- On any unrecoverable failure (ingestion halt, budget exceeded, all retries exhausted), an alert is dispatched
- Alert channel is configurable: email (via Gmail MCP) or Slack webhook
- Alert contains: run_id, stage where failure occurred, error summary

**Final constraint audit:**
- A checklist review of every constraint in `problemstatement.md`:
  - [ ] Public exports only — no scraping
  - [ ] Max 5 themes
  - [ ] Pulse ≤ 250 words
  - [ ] No PII in any artifact
  - [ ] All Google Workspace via MCP servers only

**Runbook:**
- A runbook documents: how to configure the agent for a new environment, how to run it manually, how to interpret run logs, and how to troubleshoot the most common failure modes (MCP server not running, export file in wrong format, LLM rate limit hit)

### Key Decisions Made at This Phase
- Alert channel is configurable — decided against hardcoding email or Slack (see D-009 pending)
- Token budget is a configurable guardrail, not a hard-coded constant
- Runbook is the acceptance test for maintainability — if a new team member cannot use it, it is not done

### Deliverables
- Security audit checklist (signed off)
- Token budget config and guardrail logic in place
- Failure alerting wired and tested
- Final constraint audit against `problemstatement.md` — all constraints confirmed
- Runbook written and walkthrough-tested

---

## Timeline Summary

| Phase | Focus | Key Risk | Estimated Effort |
|---|---|---|---|
| 1 | Review Ingestion | Export format changes from Apple/Google | 2–3 days |
| 2 | Theme Analysis | LLM output quality and PII leakage | 3–4 days |
| 3 | Pulse Generation | Word limit enforcement, output quality | 2–3 days |
| 4 | MCP Server Setup | OAuth setup complexity, MCP availability | 3–5 days |
| 5 | Agent Orchestration | Error handling edge cases, scheduling | 3–4 days |
| 6 | Hardening | PII audit completeness, runbook clarity | 2–3 days |

**Total estimated:** 15–22 days

**Critical path:** Phase 4 (MCP setup) has the highest uncertainty due to external dependencies (Google Cloud Console configuration, MCP server compatibility). Begin Phase 4 setup in parallel with Phase 3 if possible to avoid blocking the pipeline.
