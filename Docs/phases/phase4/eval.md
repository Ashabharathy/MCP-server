# Phase 4 Evaluation — MCP Server Setup & Google Workspace Integration

**Phase:** 4 — MCP Server Setup & Google Workspace Integration
**Status:** ⬜ PENDING
**Exit Criteria:** All tests below must pass before Phase 5 begins.

---

## Evaluation Summary

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| P4-T1 | Google Docs MCP server responds to tool call | `create_document` returns a valid doc URL | ⬜ PENDING |
| P4-T2 | Google Docs update is idempotent | Calling `update_document` twice does not create duplicate docs | ⬜ PENDING |
| P4-T3 | Gmail MCP server responds to tool call | `draft_email` returns draft ID without sending | ⬜ PENDING |
| P4-T4 | Delivery module handles MCP server down gracefully | Error logged, run continues as partial, no crash | ⬜ PENDING |
| P4-T5 | No credentials in agent codebase | Automated scan finds zero API keys/OAuth tokens in repo | ⬜ PENDING |
| P4-T6 | Docs delivery writes full pulse markdown | Created doc contains all three sections (Themes, Voices, Actions) | ⬜ PENDING |
| P4-T7 | Gmail delivery creates draft with correct subject and body | Draft subject matches `GROWW Weekly Pulse — YYYY-MM-DD` format | ⬜ PENDING |
| P4-T8 | MCP config template is safe to commit | Template contains no real credentials, only placeholder values | ⬜ PENDING |

---

## Detailed Test Cases

### P4-T1 — Google Docs MCP Server Responds

**Goal:** Confirm the Google Docs MCP server is running and the `create_document` tool works end-to-end.

**Setup:**
- MCP server configured with valid OAuth credentials
- Server running locally or at configured endpoint

**Steps:**
1. Call `create_document` tool via MCP with title `"Test Pulse Doc"` and body `"Hello MCP"`
2. Capture response

**Expected:**
- Response contains a valid Google Docs URL (`docs.google.com/document/d/...`)
- Document is visible in Google Docs UI
- No error or timeout

**Exit:** ⬜ PENDING

---

### P4-T2 — Google Docs Update is Idempotent

**Goal:** Confirm that re-running the delivery step updates an existing doc instead of creating a duplicate.

**Setup:**
- An existing Google Doc ID available (from P4-T1 or a pre-created doc)

**Steps:**
1. Call `update_document` with known `doc_id` and pulse content version A
2. Verify content is updated to version A
3. Call `update_document` again with pulse content version B on same `doc_id`
4. Verify content is updated to version B; confirm no new document was created

**Expected:**
- Only one document exists with the given ID after both calls
- Content reflects the latest version B
- No duplicate documents in Google Drive

**Exit:** ⬜ PENDING

---

### P4-T3 — Gmail MCP Server Responds with Draft (No Send)

**Goal:** Confirm the Gmail MCP server creates a draft without sending it.

**Setup:**
- Gmail MCP server configured and running
- OAuth consent covers `gmail.compose` scope

**Steps:**
1. Call `draft_email` tool with `to`, `subject`, and `body` fields
2. Check Gmail Drafts folder

**Expected:**
- Draft appears in Gmail Drafts (not Sent)
- Draft subject matches the specified subject
- No email is delivered to the recipient

**Exit:** ⬜ PENDING

---

### P4-T4 — Delivery Module Handles MCP Server Unavailability

**Goal:** Confirm the agent does not crash when an MCP server is unreachable.

**Setup:**
- Stop or block the MCP server so it returns a connection error

**Steps:**
1. Run the delivery module with MCP server unavailable
2. Observe behavior

**Expected:**
- Error is logged with stage context (`delivery/docs` or `delivery/gmail`)
- Run log shows `delivery_status: "partial"`
- Process exits cleanly with non-zero status code (no unhandled exception)

**Exit:** ⬜ PENDING

---

### P4-T5 — No Credentials in Agent Codebase

**Goal:** Confirm that OAuth tokens, client secrets, API keys, and bearer tokens do not appear anywhere in tracked files.

**Scan Patterns:**
```
client_secret, client_id, access_token, refresh_token,
GOOGLE_API_KEY, AIza, ya29, Bearer, private_key
```

**Steps:**
1. Run credential scan against all files in the repo (excluding `.gitignore`-d paths)
2. Review output

**Expected:**
- Zero matches across all files
- `config/mcp-config-template.json` contains only placeholder strings (e.g., `"<YOUR_CLIENT_ID>"`)

**Exit:** ⬜ PENDING

---

### P4-T6 — Google Doc Contains Full Pulse Structure

**Goal:** Confirm the delivered Google Doc contains all three required sections.

**Steps:**
1. Run full Phase 1–4 pipeline on sample data
2. Retrieve the created Google Doc content via MCP `get_document` call

**Expected:**
- Doc contains headers: `Top 3 Themes`, `User Voices`, `Action Ideas`
- At least 3 themes listed, each with review count
- At least 3 quotes (one per top theme)
- At least 3 action suggestions
- Word count of pulse body ≤ 250 words

**Exit:** ⬜ PENDING

---

### P4-T7 — Gmail Draft Has Correct Subject Format

**Goal:** Confirm the drafted email uses the standard GROWW Weekly Pulse subject format.

**Steps:**
1. Run delivery module (Phases 1–4 on sample data)
2. Check Gmail Drafts for the created draft

**Expected:**
- Subject line matches: `GROWW Weekly Pulse — YYYY-MM-DD` (current week's date)
- Body is plain text (not markdown)
- Recipient matches `--recipient` config value

**Exit:** ⬜ PENDING

---

### P4-T8 — MCP Config Template is Credential-Free

**Goal:** Confirm `config/mcp-config-template.json` is safe to commit to version control.

**Steps:**
1. Open `config/mcp-config-template.json`
2. Inspect all fields

**Expected:**
- All credential fields contain placeholder values like `"<YOUR_CLIENT_ID>"`, `"<YOUR_CLIENT_SECRET>"`, `"<YOUR_REFRESH_TOKEN>"`
- No real tokens or secrets present
- A comment block or README note explains where to get actual credentials

**Exit:** ⬜ PENDING

---

## Phase 4 Exit Gate

| Gate | Condition | Status |
|------|-----------|--------|
| MCP servers running | P4-T1 and P4-T3 pass | ⬜ |
| Delivery module integrated | P4-T4, P4-T6, P4-T7 pass | ⬜ |
| Security clear | P4-T5 and P4-T8 pass | ⬜ |
| Idempotency confirmed | P4-T2 passes | ⬜ |

**Phase 4 Exit Status: ⬜ PENDING — Begin Phase 5 only after all gates are green.**
