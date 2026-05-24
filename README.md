# GROWW Weekly Review Pulse Agent

An AI-powered agent that automatically analyzes app store reviews and generates a concise weekly pulse note for the GROWW Mutual Fund app.

## Overview

This agent pulls recent App Store and Google Play Store reviews, groups them into themes, generates a one-page weekly pulse note, and saves it to Google Docs while drafting a summary email via Gmail. All Google Workspace interactions are handled through MCP (Model Context Protocol) servers.

## What It Does

The Weekly Review Pulse contains:
- **Top Themes** — Up to 5 grouped categories (e.g., onboarding, KYC, payments, statements, withdrawals)
- **Real User Quotes** — 3 verbatim excerpts (no PII — no usernames, emails, or IDs)
- **Three Action Ideas** — Concrete, prioritized improvement suggestions

## Architecture

The project is built in six sequential phases:

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Foundation & Review Ingestion | ✅ Implemented |
| 2 | Theme Analysis | 🚧 Pending |
| 3 | Pulse Generation | 🚧 Pending |
| 4 | MCP Server Setup & Google Workspace Integration | 🚧 Pending |
| 5 | Agent Orchestration & Full Pipeline | 🚧 Pending |
| 6 | Hardening & Production Readiness | 🚧 Pending |

See [Docs/implementation-plan.md](Docs/implementation-plan.md) for detailed phase specifications.

## Project Structure

```
.
├── agent.py              # Main orchestrator (Phase 5 stub)
├── run_phase1.py         # Phase 1 execution script
├── ingestion/            # Review ingestion module
├── analyzer/             # Theme analysis module
├── generator/            # Pulse generation module
├── delivery/             # MCP delivery wrappers
├── config/               # Configuration files
├── prompts/              # LLM prompt templates
├── tests/                # Test suite
├── Docs/                 # Documentation
│   ├── problemstatement.md
│   ├── implementation-plan.md
│   ├── architecture.md
│   ├── decision.md
│   └── eval.md
└── credentials.json      # Credentials (not tracked in git)
```

## Current Status

**Phase 1 (Review Ingestion)** is implemented and ready to run.

### Running Phase 1

```bash
python run_phase1.py
```

This will:
- Load Google Play Store reviews from `ingestion/sample_data/playstore_sample.csv`
- Filter reviews for the last 12 weeks (configurable)
- Apply date filtering and deduplication
- Output results to `ingestion/output/reviews.json`
- Display a console summary with rating distribution and sample records

### Configuration

Edit `run_phase1.py` to adjust:
- `WEEKS`: Look-back window (default: 12 weeks)
- `REF_DATE`: Reference date for the window (default: current UTC time)
- `PLAYSTORE_CSV`: Path to the Play Store export file

## Requirements

- Python 3.8+
- Dependencies (see `requirements.txt` when created)
- LLM access (for phases 2-3)
- MCP servers for Google Docs and Gmail (for phase 4)

## Key Constraints

- **Public exports only** — No scraping behind logins
- **Maximum 5 themes** — Enforced at prompt and code level
- **Pulse ≤ 250 words** — Scannable format for quick reading
- **No PII** — No usernames, emails, or user IDs in any artifacts
- **MCP-only Google Workspace** — All Docs and Gmail interactions via MCP servers

## Documentation

- [Problem Statement](Docs/problemstatement.md) — Detailed requirements and constraints
- [Implementation Plan](Docs/implementation-plan.md) — Six-phase build plan with decisions
- [Architecture](Docs/architecture.md) — System architecture and data flow
- [Decision Log](Docs/decision.md) — Key architectural decisions
- [Evaluation Criteria](Docs/eval.md) — Exit criteria for each phase

## Who This Helps

| Audience | Value |
|----------|-------|
| Product / Growth Teams | Understand what to fix next |
| Support Teams | Know what users are saying and acknowledge |
| Leadership | Quick weekly health pulse |

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
