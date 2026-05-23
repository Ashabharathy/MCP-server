# Decision Log — GROWW Weekly Review Pulse Agent

## Purpose

This file captures the significant technical and logical decisions made while designing and building the Weekly Review Pulse agent. Only decisions that had real alternatives, meaningful trade-offs, or lasting architectural impact are recorded here. Routine implementation choices are not logged.

Each entry follows a consistent format so future contributors understand not just *what* was decided, but *why*, and what the ongoing consequences are.

---

## Decision Template

```
### D-XXX — [Short Title]
- **Date:** YYYY-MM-DD
- **Status:** Decided | Superseded | Under Review
- **Phase:** Which implementation phase this decision belongs to
- **Context:** What situation forced this decision?
- **Options Considered:** What real alternatives were evaluated?
- **Decision:** What was chosen?
- **Rationale:** The primary reasons for this choice over alternatives.
- **Consequences:** Trade-offs, follow-on constraints, or things this decision makes harder.
```

---

## Decisions

---

### D-001 — MCP Servers as the Exclusive Google Workspace Integration Path

- **Date:** 2026-05-22
- **Status:** Decided
- **Phase:** Phase 4

- **Context:** The agent needs to write content to Google Docs and send a Gmail draft. There are two structurally different ways to do this: call the Google REST APIs directly from the agent application code (handling OAuth 2.0 tokens in application config), or route all Google Workspace interactions through MCP servers that expose tool calls to the agent.

- **Options Considered:**
  1. **Direct Google REST API calls** — the agent holds OAuth tokens in its environment config, calls the Docs and Gmail APIs directly. Simpler to set up initially; no MCP dependency.
  2. **MCP Server integration** — the agent calls MCP tools (`create_document`, `draft_email`); MCP servers own all credentials and API communication.

- **Decision:** MCP servers exclusively. The agent application code never holds credentials and never calls Google APIs directly.

- **Rationale:**
  - This is stated as a hard constraint in the problem statement — the build specifically requires MCP server integration, not direct APIs. This is not optional.
  - MCP is the architecturally correct integration pattern for LLM agent tool use. Tools are exposed as callable functions, keeping the agent code clean and Google-API-agnostic.
  - Credential isolation: if the MCP server's credentials are rotated or revoked, the agent code requires zero changes. This is a significant operational advantage.
  - Future-proofing: if Google's API contract changes, only the MCP server adapter needs updating — the agent's delivery module is untouched.

- **Consequences:**
  - MCP server setup (Phase 4) is a prerequisite before any end-to-end delivery can be tested. This adds a hard dependency on external infrastructure that doesn't exist yet.
  - OAuth consent screens must be configured in Google Cloud Console as a one-time manual step — this is outside the agent codebase.
  - If the MCP server is unavailable at runtime, delivery fails gracefully (logged as partial), not catastrophically. The pipeline must handle this case.

---

### D-002 — Official App Store Exports Only — No Scraping

- **Date:** 2026-05-22
- **Status:** Decided
- **Phase:** Phase 1

- **Context:** The agent needs a source of GROWW app reviews from the App Store and Play Store. There are multiple ways to obtain these: scrape the store web pages, use a third-party review aggregator service, or use the official export mechanisms provided by App Store Connect and Google Play Console.

- **Options Considered:**
  1. **Web scraping** — automated parsing of App Store or Play Store review pages. Can be built quickly but is fragile and legally risky.
  2. **Third-party aggregator** — services like AppFollow, Appbot, or Sensor Tower provide review data via API. Adds external cost and dependency.
  3. **Official CSV exports** — App Store Connect and Google Play Console both provide downloadable CSV exports of reviews. Free, structured, compliant.

- **Decision:** Official CSV/JSON exports only. The ingestion module accepts files dropped from App Store Connect and Google Play Console. No scraping, no third-party services.

- **Rationale:**
  - Scraping violates Apple's and Google's terms of service. Legal risk is non-negotiable to eliminate.
  - Third-party aggregators introduce cost and an external dependency that is not needed when official exports exist.
  - Official exports are structured, stable, and free. The format changes rarely.
  - This is explicitly required by the problem statement: "use public review exports only — no scraping behind logins."

- **Consequences:**
  - Someone on the team must manually export CSVs from App Store Connect and Play Console each week, or this step must be automated via the official store APIs (if available for the account tier). This is an operational dependency.
  - If Apple or Google changes their export format, the ingestion parsers need updating — but this happens rarely and is low-risk.

---

### D-003 — Theme Count Enforced at Both Prompt and Code Level (Dual Enforcement)

- **Date:** 2026-05-22
- **Status:** Decided
- **Phase:** Phase 2

- **Context:** The problem statement requires reviews to be grouped into a maximum of 5 themes. The theme analyzer uses an LLM to do this clustering. The question is: how strictly do we enforce the 5-theme limit given that LLMs are non-deterministic and can violate prompt instructions?

- **Options Considered:**
  1. **Prompt-only** — instruct the LLM to return ≤ 5 themes. Simple, but LLMs can and do ignore this in edge cases (especially with diverse review sets).
  2. **Code-only enforcement** — accept whatever the LLM returns and truncate/merge to 5 in post-processing. Reliable but wastes computation on excess themes the LLM generates.
  3. **Dual enforcement** — instruct the LLM in the prompt AND enforce the limit in post-processing code by merging smallest themes.

- **Decision:** Dual enforcement. The prompt explicitly states the 5-theme maximum. Post-processing code independently enforces it by sorting themes by review count (descending) and merging the smallest themes into the nearest semantically adjacent theme until ≤ 5 remain.

- **Rationale:**
  - LLMs are probabilistic. Relying solely on prompt instructions for a hard constraint is not production-safe.
  - Code-level enforcement is deterministic — it will always produce ≤ 5 themes regardless of LLM behavior.
  - Dual enforcement gives us the best of both: the LLM tries to respect the constraint (so merging is rarely needed), and code catches the cases where it doesn't.

- **Consequences:**
  - Post-processing logic must handle theme merging in a semantically reasonable way — not just arbitrary truncation. Merging strategy: smallest theme by review count is merged into the most semantically similar larger theme (determined by a second LLM call or keyword overlap).
  - When themes are merged by code, this event is logged so it is auditable.

---

### D-004 — Two-Pass PII Stripping: Regex First, Then LLM

- **Date:** 2026-05-22
- **Status:** Decided
- **Phase:** Phase 2 and Phase 3

- **Context:** User reviews can contain personally identifiable information (PII) — reviewer names, email addresses, phone numbers, city/state references tied to a specific individual, or phrasing like "I, Anita from Pune, tried to..." The problem statement prohibits any PII in any artifact (pulse document, email, logs). The question is how to reliably detect and strip PII without manual review.

- **Options Considered:**
  1. **Manual review before delivery** — a human checks the pulse before it goes to Google Docs and Gmail. Reliable but defeats the automation purpose and doesn't scale.
  2. **Regex-only** — pattern match for emails, phone numbers, numeric IDs. Fast and cheap but completely misses names, locations, and natural-language PII.
  3. **LLM-only PII detection** — prompt an LLM to identify and redact PII. Handles natural language well but is slower, more expensive, and can miss structured patterns.
  4. **Regex + LLM in sequence** — run regex first to catch structured PII cheaply and quickly, then run an LLM pass to catch contextual/natural-language PII that regex cannot detect.

- **Decision:** Two-pass approach: regex first, then LLM. Applied at two points: after quote extraction in Phase 2 (before quotes are stored), and after pulse generation in Phase 3 (as a final safety net).

- **Rationale:**
  - Neither approach alone is sufficient. Regex misses natural-language PII; LLM-only is slower and misses structured patterns like +91-XXXXXXXXXX.
  - Regex is deterministic and cheap — it handles the easy cases (emails, phone numbers, numeric IDs) instantly.
  - LLM pass handles the hard cases (names, locations embedded in narrative text) that regex cannot.
  - Applying PII stripping at both Phase 2 (quote extraction) and Phase 3 (pulse generation output) gives defense-in-depth — the generator could theoretically reintroduce context from the original review text.

- **Consequences:**
  - Adds incremental LLM token cost for the PII detection pass. Estimated to be minor compared to the main analysis, but monitored via token logging.
  - The LLM PII prompt must be carefully designed to avoid false positives (stripping non-PII terms like city names used in a general sense) and false negatives (missing subtle PII).

---

### D-005 — Retry-Then-Truncate Strategy for the 250-Word Pulse Limit

- **Date:** 2026-05-22
- **Status:** Decided
- **Phase:** Phase 3

- **Context:** The pulse must be ≤ 250 words. LLMs consistently exceed word count limits specified in prompts, especially when the content is dense with themes and action items. We need a reliable mechanism to guarantee the output is within the limit.

- **Options Considered:**
  1. **Prompt-only constraint** — instruct the LLM to stay within 250 words. Simple, but LLMs are bad at counting words and frequently violate this even when explicitly told.
  2. **Hard truncation** — cut the generated text at the 250-word boundary. Guaranteed to work but will produce mid-sentence cuts and structurally broken output.
  3. **Retry loop only** — if over 250 words, re-prompt with a stricter instruction. Preserves quality but could loop indefinitely or always fail on certain inputs.
  4. **Retry then truncate** — retry up to 2 times with an increasingly strict prompt; if still over after retries, truncate — but truncate at a structural boundary (end of the last complete bullet or section), not mid-sentence.

- **Decision:** Retry loop (max 2 retries with stricter prompt each time), then structured truncation as a final fallback. Truncation priority: preserve themes section fully, then quotes, then trim from action ideas.

- **Rationale:**
  - Prompt-only is not reliable enough for a hard limit.
  - Retry first gives the LLM a chance to self-correct and produce better output, which is preferable to mechanical truncation.
  - Two retries is a deliberate balance: more retries add latency and cost; fewer may not resolve stubborn overages.
  - Structured truncation (not mid-sentence) ensures the output is still coherent even in the worst case.

- **Consequences:**
  - In edge cases, up to 3 LLM calls are made for pulse generation (initial + 2 retries). This is acceptable for a weekly batch job with low real-time pressure.
  - Truncation events are logged so we can track how often the retry loop fails and tune the prompt accordingly.

---

### D-006 — LLM Provider Is Configurable (No Vendor Lock-in)

- **Date:** 2026-05-22
- **Status:** Decided
- **Phase:** Across all LLM-using phases (2, 3)

- **Context:** The pipeline uses an LLM for three tasks: theme clustering (Phase 2), pulse generation (Phase 3), and PII detection passes. We need to choose which LLM to use. The obvious options are GPT-4o (OpenAI), Claude 3.5 Sonnet (Anthropic), and Gemini (Google). Each has different pricing, rate limits, and output quality characteristics for this specific task.

- **Options Considered:**
  1. **Hardcode a specific model** — pick one provider (e.g., OpenAI GPT-4o), build directly against their SDK. Simplest to implement initially.
  2. **Abstract via config** — the model provider and model name are set in the agent's config file. The agent code calls a provider-agnostic wrapper. Switching providers requires only a config change.

- **Decision:** Provider-agnostic design. The LLM provider, model name, and API key are externalized in config (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`). The default recommended starting model is GPT-4o or Claude 3.5 Sonnet (to be validated in Phase 2 testing).

- **Rationale:**
  - LLM pricing and quality evolve rapidly. Locking into one provider today may mean unnecessary cost or quality issues in 3 months.
  - Provider-agnostic design costs very little extra effort — it is a config abstraction, not a full adapter framework.
  - The team can benchmark both GPT-4o and Claude 3.5 on the theme clustering and pulse generation tasks during Phase 2/3 and pick the best performer without rewriting code.

- **Consequences:**
  - Prompt templates may perform slightly differently across models. All prompts must be tested against the chosen model before go-live. If the model is changed, prompt validation is required.
  - `LLM_API_KEY` in config must be treated as a secret and excluded from version control (added to `.gitignore`).

---

## Pending Decisions

Decisions still to be made as the project progresses:

| ID | Decision Topic | Context | Target Phase |
|---|---|---|---|
| D-007 | MCP server hosting: local vs. cloud | If MCP servers run locally, they must be running when the scheduled agent runs. Cloud hosting removes this operational dependency but adds infrastructure cost. | Phase 4 |
| D-008 | Gmail behavior: draft vs. auto-send | Current default is draft (human reviews before sending). If the team gains confidence in output quality, auto-send could be enabled. Needs a quality threshold or approval gate design. | Phase 5 |
| D-009 | Pipeline failure alert channel | Email (via Gmail MCP, self-referential) vs. Slack webhook vs. PagerDuty. Depends on team tooling preferences. | Phase 6 |
| D-010 | Weekly export automation vs. manual hand-off | Manual export from App Store Connect / Play Console weekly is operational overhead. Automating via official store APIs (if available) would remove the manual step but adds auth complexity for a different system. | Phase 6 |
