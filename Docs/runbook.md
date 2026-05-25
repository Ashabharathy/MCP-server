# GROWW Weekly Review Pulse Agent — Runbook

This runbook documents how to configure, run, monitor, and troubleshoot the GROWW Weekly Review Pulse Agent.

---

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Configuration](#configuration)
3. [Running the Agent](#running-the-agent)
4. [Interpreting Run Logs](#interpreting-run-logs)
5. [Troubleshooting](#troubleshooting)
6. [Security Auditing](#security-auditing)
7. [Maintenance](#maintenance)

---

## Environment Setup

### Prerequisites

- Python 3.8 or higher
- Groq API key (for LLM calls)
- Google OAuth tokens (for Google Docs and Gmail)
- Review export files (CSV format from App Store and/or Google Play Store)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd MCP

# Install dependencies
pip install -r requirements.txt
```

### Required Environment Variables

Set the following environment variables:

```bash
# Groq API key (required)
export GROQ_API_KEY="gsk_..."

# Google credentials (required for delivery)
export GOOGLE_DOC_ID="your-google-doc-id"
export GDRIVE_TOKEN_JSON='{"token": "...", "refresh_token": "...", ...}'
export GMAIL_TOKEN_JSON='{"token": "...", "refresh_token": "...", ...}'
export GMAIL_RECIPIENT="your-email@example.com"

# Alerting (optional)
export ALERT_CHANNEL="email"  # or "slack"
export ALERT_RECIPIENT="alert-recipient@example.com"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
```

---

## Configuration

### Review Export Files

Place your review export CSV files in the appropriate locations:

```
ingestion/sample_data/
├── playstore_sample.csv  # Google Play Store reviews
└── appstore_sample.csv   # App Store reviews (optional)
```

### Configurable Parameters

The agent supports the following configurable parameters via CLI flags:

| Parameter | Default | Description |
|---|---|---|
| `--weeks` | 8 | Number of weeks to look back for reviews (1-52) |
| `--dry-run` | False | Skip delivery stages, output pulse to stdout/file only |
| `--doc-id` | None | Google Doc ID to update (overrides GOOGLE_DOC_ID env var) |
| `--recipient` | None | Email address for Gmail draft (overrides GMAIL_RECIPIENT env var) |
| `--model` | None | LLM model override |
| `--token-budget` | 50000 | Maximum LLM tokens to use per run |

---

## Running the Agent

### Dry Run (Test Mode)

Run the agent without delivering to Google Docs or Gmail:

```bash
python agent.py --dry-run --weeks 8
```

This is useful for:
- Testing the pipeline end-to-end
- Validating configuration
- Auditing generated content before delivery
- Debugging without side effects

### Full Pipeline Run

Run the agent with full delivery to Google Docs and Gmail:

```bash
python agent.py --weeks 8 --doc-id YOUR_DOC_ID --recipient YOUR_EMAIL
```

### Custom Token Budget

Run with a custom token budget to control LLM costs:

```bash
python agent.py --weeks 8 --token-budget 100000
```

### Scheduling

The agent is designed to be stateless and can be scheduled via cron or cloud scheduler:

```bash
# Weekly cron job (every Monday at 9 AM)
0 9 * * 1 cd /path/to/MCP && python agent.py --weeks 8 >> logs/cron.log 2>&1
```

---

## Interpreting Run Logs

### Run Log Location

Run logs are written to `logs/run_<uuid>.json` after each run.

### Run Log Structure

```json
{
  "run_id": "uuid",
  "run_mode": "full" | "dry-run",
  "run_at": "ISO-8601 timestamp",
  "config": {
    "weeks": 8,
    "dry_run": false,
    "doc_id": "...",
    "recipient": "...",
    "model": null,
    "token_budget": 50000
  },
  "stages": {
    "ingestion": {
      "success": true,
      "duration": 0.69,
      "error": null,
      "output": {
        "review_count": 54,
        "date_range": {"from": "...", "to": "..."}
      }
    },
    "analysis": {
      "success": true,
      "duration": 8.77,
      "error": null,
      "output": {
        "theme_count": 5,
        "llm_tokens_used": 5852
      }
    },
    "generation": {
      "success": true,
      "duration": 12.47,
      "error": null,
      "output": {
        "pulse_word_count": 169,
        "llm_tokens_used": 915
      }
    },
    "delivery": {
      "success": true,
      "duration": 5.23,
      "error": null,
      "output": {
        "docs_delivery_status": "success",
        "gmail_delivery_status": "success",
        "doc_url": "https://docs.google.com/document/d/...",
        "draft_id": "..."
      }
    }
  },
  "summary": {
    "date_range": {"from": "...", "to": "..."},
    "review_count": 54,
    "theme_count": 5,
    "pulse_word_count": 169,
    "docs_delivery_status": "success",
    "gmail_delivery_status": "success",
    "doc_url": "https://docs.google.com/document/d/...",
    "duration_seconds": 21.65,
    "tokens_used": 6767,
    "token_budget": 50000,
    "errors": []
  },
  "status": "success" | "partial"
}
```

### Status Values

- `success`: All stages completed successfully
- `partial`: Some stages failed, but pipeline continued (e.g., delivery failed after generation succeeded)

### Key Metrics to Monitor

- `tokens_used`: Track LLM token usage to manage costs
- `duration_seconds`: Monitor pipeline performance
- `review_count`: Ensure review volume is as expected
- `errors`: Investigate any errors that appear

---

## Troubleshooting

### Common Failure Modes

#### 1. MCP Server Not Running

**Symptoms:**
- Delivery stage fails with connection errors
- Error: "Failed to connect to MCP server"

**Resolution:**
- Verify MCP server is running and accessible
- Check MCP server logs for errors
- Ensure MCP server credentials are valid
- Test MCP server connectivity independently

#### 2. Export File in Wrong Format

**Symptoms:**
- Ingestion stage fails
- Error: "Failed to parse CSV" or "Invalid review format"

**Resolution:**
- Verify CSV file format matches expected schema
- Check for missing required columns (rating, title, text, date)
- Ensure date format is ISO-8601 or compatible
- Validate CSV encoding (UTF-8)

#### 3. LLM Rate Limit Hit

**Symptoms:**
- Analysis or generation stage fails
- Error: "429 Too Many Requests" from Groq API

**Resolution:**
- Wait for rate limit to reset (typically 1-5 minutes)
- Reduce batch size in analyzer configuration
- Implement exponential backoff (already implemented)
- Consider upgrading to higher rate limit tier

#### 4. Token Budget Exceeded

**Symptoms:**
- Pipeline halts mid-run
- Error: "Token budget exceeded"

**Resolution:**
- Increase `--token-budget` parameter
- Reduce review sample size
- Reduce batch size in analyzer
- Monitor token usage trends and adjust budget accordingly

#### 5. Google Credentials Expired

**Symptoms:**
- Delivery stage fails with authentication errors
- Error: "401 Unauthorized" or "Invalid credentials"

**Resolution:**
- Refresh OAuth tokens
- Update `GDRIVE_TOKEN_JSON` and `GMAIL_TOKEN_JSON` environment variables
- Verify token scopes include required permissions
- Check token expiration dates

#### 6. No Reviews Found

**Symptoms:**
- Ingestion stage fails
- Error: "No reviews loaded - ingestion failed"

**Resolution:**
- Verify review export file contains data
- Check date range (weeks parameter) - may need to increase
- Verify date filter is not excluding all reviews
- Check review export date format

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
export LOG_LEVEL=DEBUG
python agent.py --dry-run --weeks 8
```

### Isolating Stages

Run individual phase scripts to isolate issues:

```bash
# Test ingestion only
python run_phase1.py

# Test analysis only
python run_phase2.py

# Test generation only
python run_phase3.py

# Test delivery only
python run_phase4.py
```

---

## Security Auditing

### Running Security Audit

Run the security audit script to scan for credentials:

```bash
python scripts/security_audit.py
```

The audit checks for:
- API keys in source files
- OAuth tokens in source files
- Missing .gitignore patterns
- Credential files in repository

### Manual PII Audit

Periodically review logs and outputs for PII:

1. Check recent run logs in `logs/` directory
2. Review generated pulse content in `generator/output/pulse.json`
3. Verify no usernames, emails, or user IDs appear
4. Check theme analysis output in `analyzer/output/themes.json`

### Credential Rotation

Rotate credentials regularly:

1. Generate new OAuth tokens
2. Update environment variables
3. Test with dry-run mode
4. Deploy to production

---

## Maintenance

### Regular Tasks

**Weekly:**
- Review run logs for errors
- Monitor token usage trends
- Check Google Doc for successful updates
- Verify Gmail drafts are created

**Monthly:**
- Run security audit
- Review and rotate credentials
- Update dependencies
- Review token budget and adjust if needed

**Quarterly:**
- Review constraint audit
- Update documentation
- Review alerting configuration
- Performance tuning

### Dependency Updates

Update dependencies regularly:

```bash
pip list --outdated
pip install --upgrade <package-name>
```

### Backup and Recovery

**Run Logs:**
- Run logs are stored in `logs/` directory
- Archive old logs periodically
- Consider log rotation for long-running deployments

**Configuration:**
- Document all environment variables
- Backup configuration files
- Version control configuration templates

---

## Contact and Support

For issues or questions:
1. Check this runbook first
2. Review recent run logs
3. Check GitHub issues
4. Contact the development team

---

## Appendix

### Phase Scripts Reference

| Script | Purpose | Output |
|---|---|---|
| `run_phase1.py` | Review ingestion | `ingestion/output/reviews.json` |
| `run_phase2.py` | Theme analysis | `analyzer/output/themes.json` |
| `run_phase3.py` | Pulse generation | `generator/output/pulse.json` |
| `run_phase4.py` | Delivery | `delivery/output/delivery.json` |
| `agent.py` | Full orchestrator | `logs/run_<uuid>.json` |

### Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key for LLM calls |
| `GOOGLE_DOC_ID` | Yes | Google Doc ID to update |
| `GDRIVE_TOKEN_JSON` | Yes | OAuth token for Google Drive/Docs |
| `GMAIL_TOKEN_JSON` | Yes | OAuth token for Gmail |
| `GMAIL_RECIPIENT` | Yes | Email address for Gmail draft |
| `ALERT_CHANNEL` | No | Alert channel: "email" or "slack" |
| `ALERT_RECIPIENT` | No | Alert recipient email |
| `SLACK_WEBHOOK_URL` | No | Slack webhook URL for alerts |

### Output Files Reference

| File | Location | Description |
|---|---|---|
| Reviews | `ingestion/output/reviews.json` | Filtered reviews from ingestion |
| Themes | `analyzer/output/themes.json` | Identified themes with quotes |
| Pulse | `generator/output/pulse.json` | Generated pulse in multiple formats |
| Delivery | `delivery/output/delivery.json` | Delivery results and metadata |
| Run Log | `logs/run_<uuid>.json` | Complete run log with all metrics |
