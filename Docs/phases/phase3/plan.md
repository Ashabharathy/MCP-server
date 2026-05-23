# Phase 3 — Pulse Generation

## Goal
Transform the themed analysis into a polished, scannable weekly pulse note that is ≤ 250 words — suitable for leadership, product, and support teams to read in under two minutes.

---

## Context & Rationale

The weekly pulse is the primary deliverable of the entire system. It must be concise enough to be read quickly (≤ 250 words), structured enough to be scannable (headers, bullets), and grounded in real user language (actual quotes). An LLM is ideal for this generation task because it can write in a clear, professional style given structured inputs.

The 250-word limit is a hard constraint from the problem statement. LLMs often exceed word limits even when instructed, so we enforce this with a retry-then-truncate strategy: if the first generation exceeds 250 words, we re-prompt with a stricter instruction (max 2 retries). If still over, we truncate — preserving structure priority: themes first, then quotes, then action ideas.

---

## What We Are Building

### Pulse Structure
Every generated pulse contains exactly three sections:

**Top 3 Themes** — one-sentence summary per theme with review count context
**User Voices** — 3 anonymized user quotes (one per top theme)
**Action Ideas** — 3 specific, concrete improvement suggestions derived from the themes

### Prompt Design for Generation
The prompt receives the top 3 themes (with summaries and quotes) and instructs the LLM to:
- Write a weekly pulse in the defined structure
- Stay within 250 words
- Use plain language accessible to non-technical stakeholders
- Not repeat or invent user quotes — only use the provided ones

Prompt template: `prompts/pulse-generation-v1.txt`

### Word Count Enforcement (Retry-Then-Truncate)

```
Generate pulse
    ↓
Word count ≤ 250? ──YES──▶ Done
    ↓ NO
Retry with stricter prompt (attempt 2)
    ↓
Word count ≤ 250? ──YES──▶ Done
    ↓ NO
Retry with strictest prompt (attempt 3)
    ↓
Word count ≤ 250? ──YES──▶ Done
    ↓ NO
Hard truncate (cut from bottom of Action Ideas section first)
```

Truncation preserves section structure — never cuts mid-sentence; cuts at the last complete bullet point.

### Output Variants (Three Formats)
The pulse is produced in three formats from one generation:

| Format | Destination | Notes |
|---|---|---|
| Markdown | Google Docs (via MCP) | Headers, bullet points formatted |
| Plain text | Gmail email body | No markdown symbols |
| Structured JSON | Run log | For auditability and debugging |

### Final PII Check
Before the pulse leaves this module, a final two-pass PII scan (same as Phase 2) is applied. This is a safety net — quotes were sanitized in Phase 2, but the generation step could reintroduce context from review text in the prompt.

---

## Input / Output

**Input:** `analyzer/output/themes.json` (from Phase 2)

**Output:** `generator/output/pulse.json`
```json
{
  "run_at": "...",
  "word_count": 214,
  "llm_tokens_used": 620,
  "retry_count": 0,
  "markdown": "## GROWW Weekly Review Pulse\n...",
  "plain_text": "GROWW Weekly Review Pulse\n...",
  "themes": [...],
  "quotes": [...],
  "action_ideas": [...]
}
```

---

## Folder Structure (Phase 3)

```
MCP/
├── generator/
│   ├── __init__.py
│   ├── pulse_generator.py  ← LLM call, retry logic, word count validation
│   ├── formatter.py        ← markdown / plain text / JSON output variants
│   ├── pii_check.py        ← final PII scan (reuses Phase 2 stripper)
│   └── output/
│       └── pulse.json      ← generator output
├── prompts/
│   └── pulse-generation-v1.txt
├── run_phase3.py           ← Phase 3 runner script
└── tests/
    └── test_generator.py   ← tests for all Phase 3 eval cases
```

---

## Key Decisions Made at This Phase

| Decision | Rationale | Ref |
|---|---|---|
| Retry-then-truncate strategy (max 2 retries, then hard cut) | Retries preserve quality; truncation is the guaranteed fallback | D-005 |
| Three output formats (markdown, plain text, JSON) | Each downstream consumer (Docs, Gmail, logs) needs a different format | — |
| Final PII pass even after Phase 2 sanitized quotes | Defense-in-depth; generator can reintroduce context from prompts | — |
| Truncation cuts from Action Ideas first, not Themes | Themes are the highest-value section; they must always be complete | — |

---

## Deliverables

- [ ] `generator/` module: pulse generation, word count validation, retry logic, formatter, PII check
- [ ] `prompts/pulse-generation-v1.txt`: prompt template (filled)
- [ ] `generator/output/pulse.json`: pulse output (markdown + plain text + JSON)
- [ ] `run_phase3.py`: Phase 3 runner
- [ ] `tests/test_generator.py`: all Phase 3 eval test cases

---

## Status

**Phase 3: PENDING**
Depends on: Phase 2 complete
Input: `analyzer/output/themes.json`
