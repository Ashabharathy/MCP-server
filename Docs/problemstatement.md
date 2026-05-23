# GROWW Mutual Fund FAQ Assistant — Weekly Review Pulse

## Problem Statement

Build an AI-powered **Weekly Review Pulse** agent for the GROWW Mutual Fund app that:

1. Pulls recent App Store + Play Store reviews (last 8–12 weeks)
2. Groups them into themes
3. Generates a one-page weekly pulse note
4. Saves the note to **Google Docs** and drafts a summary **email via Gmail**

All Google Docs and Gmail interactions must be handled through **MCP (Model Context Protocol) servers** — no direct REST API calls or OAuth credential management in application code.

---

## What the Weekly Pulse Contains

- **Top Themes** — up to 5 grouped categories (e.g., onboarding, KYC, payments, statements, withdrawals)
- **Real User Quotes** — 3 verbatim excerpts (no PII — no usernames, emails, or IDs)
- **Three Action Ideas** — concrete, prioritized improvement suggestions

---

## Who This Helps

| Audience | Value |
|---|---|
| Product / Growth Teams | Understand what to fix next |
| Support Teams | Know what users are saying and acknowledging |
| Leadership | Quick weekly health pulse |

---

## What You Must Build

### 1. Review Ingestion
- Import reviews from the last 8–12 weeks (fields: rating, title, text, date)
- Source: public review exports only — **no scraping behind logins**

### 2. Theme Analysis
- Group reviews into a **maximum of 5 themes**
- Label each theme clearly (e.g., KYC Issues, Payment Failures, Onboarding Friction)

### 3. Weekly Pulse Generation
- Top 3 themes with brief summaries
- 3 real user quotes (anonymized — no PII)
- 3 actionable improvement ideas
- Total length: **≤ 250 words**, scannable format

### 4. Google Docs Integration via MCP Server
- Use the **Google Docs MCP server** to create/update a Google Doc with the weekly pulse
- The MCP server handles all authentication and document operations
- No direct Google Docs REST API calls in application code

### 5. Gmail Integration via MCP Server
- Use the **Gmail MCP server** to compose and draft a summary email containing the weekly pulse note
- The email is sent to yourself / a team alias
- The MCP server handles all authentication and mail operations
- No direct Gmail REST API calls in application code

---

## MCP Servers Required

| MCP Server | Purpose |
|---|---|
| `@modelcontextprotocol/server-gdrive` or equivalent Google Docs MCP | Create and update Google Docs with the weekly pulse |
| Gmail MCP server | Draft and send the weekly pulse email |

---

## Key Constraints

- Use **public review exports only** — no scraping behind logins
- Maximum **5 themes**
- Pulse note must be **≤ 250 words** and scannable
- **No PII** — no usernames, emails, or user IDs in any artifacts
- All Google Workspace interactions via **MCP servers only** (no direct API calls)
