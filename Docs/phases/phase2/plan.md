# Phase 2 — Theme Analysis

## Goal
Use an LLM to semantically cluster the normalized reviews into a maximum of 5 meaningful themes, and extract clean, anonymized user quotes that represent each theme.

---

## Context & Rationale

The core analytical value of the agent is grouping hundreds of reviews into digestible themes so product and support teams can act on patterns rather than individual reviews. This is inherently a semantic task — keyword matching would miss paraphrased complaints, contextual issues, and cross-cutting themes.

We use an LLM for this clustering step because:
- It understands meaning and context, not just keywords
- It can be prompted to group flexibly based on what users are actually saying
- It can produce structured output (JSON) that is easy to process programmatically

The constraint of **maximum 5 themes** is enforced at two levels: in the prompt (the LLM is instructed to cluster into at most 5 groups) and in post-processing code (if the LLM returns 6+ themes, we merge the smallest ones until ≤ 5 remain). This dual enforcement is deliberate because LLMs are non-deterministic and can violate prompt instructions.

---

## What We Are Building

### Prompt Design for Clustering
The prompt instructs the LLM to:
- Read all review texts
- Identify the most common complaint or feedback categories
- Return a structured JSON response with: theme name, list of review IDs in the theme, and 2–3 representative verbatim quotes per theme
- Explicitly state the 5-theme maximum

Prompt template is version-controlled at `prompts/theme-analysis-v1.txt`.

### Structured Output (JSON Mode)
We use the LLM's JSON-mode or structured output capability to get a machine-parseable response. This avoids fragile text parsing and makes the post-processing deterministic.

Expected LLM output schema:
```json
[
  {
    "theme": "KYC Verification Issues",
    "review_count": 8,
    "review_ids": ["id1", "id2", ...],
    "quotes": [
      "KYC was rejected without any explanation.",
      "Documents uploaded three times and still pending."
    ]
  }
]
```

### Post-Processing Enforcement (≤ 5 Themes)
After receiving the LLM response:
1. Sort themes by `review_count` descending
2. If count > 5: merge smallest themes into the nearest semantically adjacent theme until ≤ 5 remain
3. Log when merging occurs (audit trail)

### PII Stripping from Quotes (Two-Pass)
Before any quote leaves this module:

**Pass 1 — Regex:** Removes structured PII
- Email addresses: `\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b`
- Indian phone numbers: `\b[6-9]\d{9}\b`
- Numeric IDs: `\b\d{8,}\b`

**Pass 2 — LLM:** Removes contextual PII
- Names embedded in narrative: "I, Ramesh from Delhi, tried to..."
- Location-tied personal references
- Prompt instructs to replace with `[user]` or `[location]` placeholders

### Token Budget Management
- Token count consumed per run is logged
- If total tokens exceed the configured budget (`llm_token_budget_per_run` in config), the run halts
- Chunked batching supported for large review volumes — reviews split into batches fitting within context window; themes merged across batches

---

## Input / Output

**Input:** `ingestion/output/reviews.json` (from Phase 1)

**Output:** `analyzer/output/themes.json`
```json
{
  "run_at": "...",
  "review_count": 30,
  "theme_count": 5,
  "llm_tokens_used": 1840,
  "themes": [
    {
      "theme": "Withdrawal & Redemption Delays",
      "review_count": 8,
      "quotes": ["...", "..."]
    }
  ]
}
```

---

## Folder Structure (Phase 2)

```
MCP/
├── analyzer/
│   ├── __init__.py
│   ├── clusterer.py       ← LLM call + structured output parsing
│   ├── post_processor.py  ← theme count enforcement, merging
│   ├── pii_stripper.py    ← regex + LLM PII removal
│   └── output/
│       └── themes.json    ← analyzer output
├── prompts/
│   └── theme-analysis-v1.txt
├── run_phase2.py          ← Phase 2 runner script
└── tests/
    └── test_analyzer.py   ← tests for all Phase 2 eval cases
```

---

## Key Decisions Made at This Phase

| Decision | Rationale | Ref |
|---|---|---|
| Dual enforcement of ≤ 5 themes (prompt + code) | LLMs are non-deterministic; code is the hard guarantee | D-003 |
| Two-pass PII stripping (regex + LLM) | Regex handles structured PII cheaply; LLM handles contextual PII | D-004 |
| LLM JSON mode for structured output | Avoids fragile text parsing; makes post-processing deterministic | — |
| Prompt templates versioned in `prompts/` | Changes are auditable; rollback is possible | — |

---

## Deliverables

- [ ] `analyzer/` module: LLM clustering call, theme post-processor, PII stripper
- [ ] `prompts/theme-analysis-v1.txt`: initial prompt template (filled)
- [ ] `analyzer/output/themes.json`: structured theme output
- [ ] `run_phase2.py`: Phase 2 runner
- [ ] `tests/test_analyzer.py`: all Phase 2 eval test cases

---

## Status

**Phase 2: PENDING**
Depends on: Phase 1 complete (✅)
Input: `ingestion/output/reviews.json`
