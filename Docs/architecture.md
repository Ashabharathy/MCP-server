# Architecture — GROWW Weekly Review Pulse Agent

## Overview

The GROWW Weekly Review Pulse Agent is an end-to-end AI pipeline. It ingests publicly exported app store reviews from the GROWW Mutual Fund app, performs LLM-driven theme clustering and pulse generation, and delivers a structured weekly note to Google Docs and Gmail — **exclusively through MCP (Model Context Protocol) servers**.

The system is designed around three principles:
1. **No direct Google API calls in application code** — all Google Workspace I/O is delegated to MCP servers
2. **No PII in any artifact** — enforced at extraction, generation, and delivery layers
3. **Minimal human intervention** — the pipeline runs on a weekly schedule end-to-end

---

## System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL SOURCES                                 │
│                                                                             │
│   App Store Connect (CSV export)     Google Play Console (CSV export)       │
└───────────────────────┬─────────────────────────────┬───────────────────────┘
                        │ public exports only          │
                        ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GROWW REVIEW PULSE AGENT                            │
│                                                                             │
│   ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐  │
│   │  Review         │    │  Theme           │    │  Pulse               │  │
│   │  Ingestion      │───▶│  Analyzer        │───▶│  Generator           │  │
│   │  Module         │    │  (LLM)           │    │  (LLM)               │  │
│   └─────────────────┘    └──────────────────┘    └──────────┬───────────┘  │
│                                                             │              │
└─────────────────────────────────────────────────────────────┼──────────────┘
                                                              │
                        ┌─────────────────────────────────────┤
                        │                                     │
                        ▼                                     ▼
           ┌────────────────────────┐           ┌────────────────────────┐
           │  Google Docs MCP       │           │  Gmail MCP             │
           │  Server                │           │  Server                │
           │  (create / update doc) │           │  (draft email)         │
           └───────────┬────────────┘           └───────────┬────────────┘
                       │                                    │
                       ▼                                    ▼
              Google Docs API                         Gmail API
              (managed by MCP)                    (managed by MCP)
```

---

## Component Breakdown

### 1. Review Ingestion Module

**Responsibility:** Load raw review exports, normalize into a clean schema, filter by date range, and prepare data for analysis.

**Inputs:**
- App Store Connect CSV export (fields: rating, title, body, date, version, country)
- Google Play Console CSV export (fields: rating, title, review text, date, reply, version)

**Processing:**
- Map each source's field names to the unified schema
- Filter records to the configured date window (default: last 8 weeks; max: 12 weeks)
- Deduplicate by review ID or by (date + title + text) fingerprint
- Strip null / empty text rows
- Normalize character encoding (UTF-8 safe output)

**Output:** List of normalized review records:
```
{
  id: string,
  rating: 1-5,
  title: string,
  text: string,
  date: ISO8601,
  source: "appstore" | "playstore"
}
```

**Constraints:**
- No login-based scraping; accepts only exported files
- No PII fields ingested (reviewer names, user IDs are excluded at this layer)

---

### 2. Theme Analyzer (LLM)

**Responsibility:** Group reviews semantically into ≤ 5 meaningful themes and extract representative, anonymized user quotes for each theme.

**Inputs:** List of normalized review records

**Processing:**
- Sample 1,000 reviews from the full dataset (stratified by rating to maintain distribution)
- Batch reviews into groups of 100 per LLM call (~10K tokens per batch) to stay within Groq's 100K tokens/day limit
- Process batches sequentially (10 batches total for 1K reviews) to stay within 30 requests/min and 1K requests/day limits
- Prompt the LLM to perform semantic clustering — returning a structured JSON response with theme name, review count, and top representative quotes per theme
- Merge themes across batches and enforce ≤ 5 themes at code level (merge smallest themes if LLM returns more)
- Run PII stripping pass on all extracted quotes (regex for structured PII + LLM pass for contextual PII)
- Sort themes by review volume (descending)

**Output:**
```
[
  {
    theme: "KYC Verification Issues",
    review_count: 42,
    quotes: ["<anonymized quote 1>", "<anonymized quote 2>"]
  },
  ...
]
```

**Key design decisions:**
- Max 5 themes enforced both in prompt instruction and in post-processing (dual enforcement — see D-003)
- PII is stripped before any quote leaves this module (see D-004)
- LLM structured output (JSON mode) used to avoid fragile text parsing

---

### 3. Pulse Generator (LLM)

**Responsibility:** Transform the themed analysis into a polished, scannable, one-page weekly note that is ≤ 250 words.

**Inputs:** Themed analysis output (top themes + quotes)

**Processing:**
- Select top 3 themes by review volume
- Prompt LLM to generate a structured weekly pulse: top themes with one-line summaries, 3 user quotes, 3 concrete action ideas
- Validate word count — if > 250 words, retry with tighter prompt (max 2 retries), then truncate as last resort preserving structure order: themes → quotes → actions
- Final PII scan on generated output before passing downstream
- Produce output in three variants: markdown (for Google Docs), plain text (for email body), structured JSON (for logging)

**Output:**
```
{
  markdown: "...",
  plain_text: "...",
  word_count: 212,
  themes: [...],
  quotes: [...],
  action_ideas: [...]
}
```

---

### 4. MCP Server Layer

The MCP server layer is the **only** path through which the agent interacts with Google Workspace. The agent orchestrator never holds credentials and never calls Google REST APIs directly.

#### 4a. Google Docs MCP Server

**Server:** `@modelcontextprotocol/server-gdrive` or a compatible Google Docs MCP implementation

**Responsibilities:**
- Authenticate with Google using OAuth 2.0 credentials stored in the MCP server's own config (not in agent code)
- Expose tools to the agent: `create_document`, `update_document`, `get_document_url`
- Accept pulse content in markdown format and write it to a Google Doc
- Return the shareable Google Doc URL to the agent

**Tool call flow:**
```
Agent ──▶ create_document(title, markdown_content)
       ◀── { doc_id, doc_url }
```

**State management:**
- On first run of the week: create a new Google Doc with date-stamped title
- On re-run within the same week: update the existing doc (idempotent)
- Doc ID is persisted in agent run state to enable updates

#### 4b. Gmail MCP Server

**Server:** Gmail-compatible MCP server

**Responsibilities:**
- Authenticate with Gmail using OAuth 2.0 credentials stored in MCP server config
- Expose tools to the agent: `draft_email`, `send_email`
- Accept email subject, plain text body, and Google Doc link
- Create a draft in Gmail (or send immediately, based on config)

**Tool call flow:**
```
Agent ──▶ draft_email(to, subject, body, doc_url)
       ◀── { draft_id, status }
```

---

### 5. Agent Orchestrator

**Responsibility:** Sequence all pipeline stages, manage configuration, handle errors and retries, log run state, and trigger scheduled runs.

**Run sequence:**
```
1. Load config (date range, recipient, doc ID if updating)
2. Ingest reviews → normalized records
3. Analyze themes → themed groups + quotes
4. Generate pulse → markdown + plain text
5. Deliver via Google Docs MCP → doc created/updated
6. Deliver via Gmail MCP → email drafted
7. Write run log (run ID, timestamps, token counts, delivery status)
```

**Modes:**
- `--run` : full pipeline including delivery
- `--dry-run` : ingest + analyze + generate; skip MCP delivery (no side effects)

**Error handling strategy:**
- Each stage is independently retried up to 3 times on transient failures
- Partial failures (e.g., Docs MCP succeeds, Gmail MCP fails) are logged separately
- Pipeline halts on ingestion failure — no partial delivery

---

## Data Flow (Detailed)

```
App Store CSV ──┐
                ├──▶ Ingestion Module ──▶ Normalized Records [ id, rating, title, text, date, source ]
Play Store CSV ─┘
                                                │
                                                ▼
                                     Theme Analyzer (LLM)
                                     ┌──────────────────────────────────────┐
                                     │  Prompt: cluster into ≤5 themes      │
                                     │  Post-process: enforce max 5         │
                                     │  PII strip: regex + LLM pass         │
                                     └──────────────────────────────────────┘
                                                │
                                    Themed Groups + Quotes (PII-free)
                                                │
                                                ▼
                                     Pulse Generator (LLM)
                                     ┌──────────────────────────────────────┐
                                     │  Select top 3 themes                 │
                                     │  Generate pulse (≤250 words)         │
                                     │  Retry if over limit (max 2 retries) │
                                     │  Final PII check                     │
                                     └──────────────────────────────────────┘
                                                │
                               ┌────────────────┴──────────────────┐
                               │                                   │
                               ▼                                   ▼
                    Google Docs MCP Server              Gmail MCP Server
                    create_document(markdown)           draft_email(plain_text + doc_url)
                               │                                   │
                               ▼                                   ▼
                       Google Doc created               Gmail draft created
                       (doc_url returned)               (draft_id returned)
                               │
                               └──────────────▶ Run Log written
                                               (run_id, timings, tokens, status)
```

---

## MCP Integration Pattern (Detail)

```
┌─────────────────────────────────┐
│        Agent Orchestrator       │
│                                 │
│  tool_call("create_document",   │
│    { title, content })          │
└──────────────┬──────────────────┘
               │ MCP protocol (stdio / SSE / HTTP)
               ▼
┌──────────────────────────────────┐
│       Google Docs MCP Server     │
│                                  │
│  - Holds OAuth 2.0 token         │
│  - Calls Google Docs REST API    │
│  - Returns { doc_id, doc_url }   │
└──────────────┬───────────────────┘
               │ HTTPS
               ▼
        Google Docs REST API
```

- Agent code has **zero knowledge** of OAuth tokens or Google API endpoints
- MCP server is the trust boundary for credentials
- If Google API contract changes, only the MCP server config/adapter is updated

---

## Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Agent Orchestration | Python (agent loop) | LLM tool-calling orchestrator |
| LLM Provider | Groq Llama-3.3-70b-versatile (Phase 2) | Rate limits: 30 req/min, 1K req/day, 12K tokens/min, 100K tokens/day |
| Review Ingestion | Python | CSV/JSON parsing, normalization, sampling to 500 reviews |
| Theme Analysis | LLM (structured JSON output) | Batched processing (50 reviews/batch) to stay within token limits |
| Pulse Generation | LLM (templated prompt) | Word-count enforced via retry loop |
| PII Stripping | Regex + LLM pass | Two-pass defense in depth |
| Google Docs Integration | Google Docs MCP Server | No direct REST API in agent code |
| Gmail Integration | Gmail MCP Server | No direct REST API in agent code |
| MCP Protocol | Model Context Protocol (MCP) | stdio or SSE transport |
| Scheduling | Cron / Cloud Scheduler | Weekly trigger |
| Logging | Structured JSON logs | run_id, phase timings, token counts |

---

## Security & Privacy Architecture

| Concern | Mitigation |
|---|---|
| PII in review quotes | Stripped at Theme Analyzer layer (regex + LLM) |
| PII in generated pulse | Final PII check before delivery |
| Google OAuth credentials in code | Stored exclusively in MCP server config |
| Credentials in logs | Log schema excludes all auth fields |
| Review scraping / ToS violation | Ingestion accepts only official CSV exports |
| Data at rest | No persistent storage of raw reviews beyond current run |

---

## Folder Structure (Target)

```
MCP/
├── Docs/
│   ├── problemstatement.md
│   ├── architecture.md
│   ├── implementation-plan.md
│   ├── eval.md
│   └── decision.md
├── ingestion/          ← Phase 1: review parsers
├── analyzer/           ← Phase 2: theme clustering
├── generator/          ← Phase 3: pulse generation
├── delivery/           ← Phase 4: MCP tool call wrappers
├── prompts/            ← versioned prompt templates
├── config/
│   └── mcp-config-template.json
├── logs/               ← structured run logs
└── agent.py            ← Phase 5: orchestrator entry point
```
