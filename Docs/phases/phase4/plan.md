# Phase 4 — MCP Server Setup & Google Workspace Integration

## Goal
Set up and validate the Google Docs MCP server and Gmail MCP server, and integrate them into the agent as the exclusive delivery mechanism. Confirm that the agent never touches Google credentials directly.

---

## Context & Rationale

This is the most infrastructure-heavy phase. The decision to use MCP servers rather than direct Google REST API calls is a core architectural constraint of the project (see D-001). MCP servers act as a trust boundary: they hold the OAuth 2.0 credentials and expose clean tools (`create_document`, `draft_email`) that the agent calls without any knowledge of the underlying API.

This phase requires one-time setup work **outside the agent codebase** — configuring OAuth consent in Google Cloud Console and setting up the MCP servers with credentials. Once done, the agent never needs to touch credentials again.

> **Note:** Phase 4 setup can and should begin in parallel with Phase 3 development to avoid it becoming a blocker. It is the highest-risk phase due to external dependencies (Google Cloud Console, MCP server compatibility).

---

## What We Are Building

### Google Docs MCP Server Setup

**Server selection:** `@modelcontextprotocol/server-gdrive` or a compatible alternative.

**One-time setup steps (outside the repo):**
1. Create a Google Cloud project
2. Enable the Google Docs API and Google Drive API
3. Configure an OAuth 2.0 consent screen
4. Create OAuth 2.0 credentials (client ID + client secret)
5. Store credentials in the MCP server's own config directory (never in the agent repo)
6. Run MCP server with credentials; complete OAuth flow once to generate token

**Required tool exposure (minimum):**

| Tool | Purpose |
|---|---|
| `create_document` | Create a new Google Doc with content |
| `update_document` | Update existing doc content (idempotent) |
| `get_document_url` | Return shareable link for a doc ID |

**Idempotency requirement:** Calling `update_document` on an existing doc replaces content, does not create a duplicate.

**State:** On first run of the week → create new doc with date-stamped title. On re-run → update existing doc using persisted doc ID.

---

### Gmail MCP Server Setup

**Server selection:** Gmail-compatible MCP server.

**One-time setup steps (outside the repo):**
1. Enable Gmail API in the same or a separate Google Cloud project
2. Configure OAuth 2.0 consent with Gmail send/draft scope
3. Store credentials in MCP server config
4. Complete OAuth flow once to generate token

**Required tool exposure (minimum):**

| Tool | Purpose |
|---|---|
| `draft_email` | Create a Gmail draft (does not send) |
| `send_email` | Send an email immediately |

**Default behavior:** `draft_email` only — the pulse email is created as a draft for human review before dispatch. `send_email` is available but not the default (see D-008 pending).

---

### Agent Delivery Module (`delivery/`)

A thin wrapper layer inside the agent codebase that:
- Translates high-level agent intents into specific MCP tool calls
- Handles MCP server unavailability gracefully: error logged, run marked as `partial`, pipeline continues
- Exposes two functions: `save_to_docs(pulse_markdown, doc_id=None)` and `draft_gmail(pulse_plain_text, doc_url, recipient)`

MCP tool call pattern:
```
Agent delivery/
    └─▶ MCP tool call (stdio / SSE)
            └─▶ Google API (managed by MCP server)
                    └─▶ Result returned to agent
```

---

### MCP Config Template (`config/mcp-config-template.json`)

Documents the shape of MCP server configuration **without real credentials**. Safe to commit. Serves as the setup guide for new environments.

---

### Credential Audit

An automated scan confirms that no API keys, OAuth tokens, or client secrets appear anywhere in:
- Agent source files (`*.py`)
- Config files tracked in the repository
- Log files

---

## Input / Output

**Input:** `generator/output/pulse.json` (from Phase 3)

**Output:**
- Google Doc created/updated → `doc_url` returned
- Gmail draft created → `draft_id` returned
- Both logged in `delivery/output/delivery_log.json`

---

## Folder Structure (Phase 4)

```
MCP/
├── delivery/
│   ├── __init__.py
│   ├── docs_client.py    ← Google Docs MCP tool call wrapper
│   ├── gmail_client.py   ← Gmail MCP tool call wrapper
│   └── output/
│       └── delivery_log.json
├── config/
│   └── mcp-config-template.json   ← already created
├── run_phase4.py                  ← Phase 4 e2e delivery test runner
└── tests/
    └── test_delivery.py           ← tests for all Phase 4 eval cases
```

---

## Key Decisions Made at This Phase

| Decision | Rationale | Ref |
|---|---|---|
| MCP servers as the only Google Workspace path | Core architectural constraint; no credentials in agent code | D-001 |
| Default Gmail behavior is "draft", not "send" | Allows human review before dispatch | D-008 (pending) |
| MCP credentials outside the agent repo entirely | Prevents accidental credential commits | D-001 |
| Idempotent document updates | Prevents duplicate docs on re-runs | — |
| MCP server unavailability = partial run, not crash | Delivery failure should not lose the generated pulse | — |

---

## Deliverables

- [ ] Running Google Docs MCP server (local or cloud-hosted)
- [ ] Running Gmail MCP server (local or cloud-hosted)
- [ ] `delivery/` module: `docs_client.py` + `gmail_client.py`
- [ ] `config/mcp-config-template.json` (already created)
- [ ] Credential audit: zero credentials in agent codebase
- [ ] At least one successful e2e delivery: pulse → Google Doc URL + Gmail draft

---

## Status

**Phase 4: PENDING**
Depends on: Phase 3 complete (can begin setup in parallel)
External dependency: Google Cloud Console OAuth setup (one-time manual step)
