"""
run_phase4.py — Execute Phase 4: MCP Delivery pipeline.

Loads pulse from Phase 3 output and delivers it to Google Docs and Gmail.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# ── logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("phase4_runner")

# ── paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
PHASE3_OUTPUT = ROOT / "generator" / "output" / "pulse.json"
PHASE4_OUTPUT_DIR = ROOT / "delivery" / "output"
PHASE4_OUTPUT_FILE = PHASE4_OUTPUT_DIR / "delivery.json"

# ── configuration ──────────────────────────────────────────────────────────
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID")
GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT")


def main() -> None:
    # Check for Google Doc ID
    if not GOOGLE_DOC_ID:
        logger.error(
            "GOOGLE_DOC_ID environment variable not set. "
            "Please set it before running Phase 4."
        )
        sys.exit(1)

    # Check for Gmail recipient
    if not GMAIL_RECIPIENT:
        logger.error(
            "GMAIL_RECIPIENT environment variable not set. "
            "Please set it before running Phase 4."
        )
        sys.exit(1)

    # Check if Phase 3 output exists
    if not PHASE3_OUTPUT.exists():
        logger.error(
            "Phase 3 output not found: %s. Please run Phase 3 first.",
            PHASE3_OUTPUT,
        )
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Phase 4 — MCP Delivery")
    logger.info("=" * 60)
    logger.info("Phase 3 output: %s", PHASE3_OUTPUT)
    logger.info("Google Doc ID: %s", GOOGLE_DOC_ID)
    logger.info("Gmail recipient: %s", GMAIL_RECIPIENT)

    # Load Phase 3 output
    logger.info("Loading pulse from Phase 3 output...")
    with open(PHASE3_OUTPUT, "r", encoding="utf-8") as f:
        phase3_data = json.load(f)

    pulse_markdown = phase3_data["generation"]["formats"]["markdown"]
    pulse_plain = phase3_data["generation"]["formats"]["plain_text"]
    logger.info("Loaded pulse from Phase 3")

    # Deliver to Google Docs
    from delivery.docs import update_google_doc

    logger.info("Delivering pulse to Google Docs...")
    docs_result = update_google_doc(
        doc_id=GOOGLE_DOC_ID,
        content=pulse_markdown,
    )

    # Draft Gmail email
    from delivery.gmail import draft_email

    logger.info("Drafting Gmail email...")
    subject = f"Weekly Review Pulse - {datetime.now().strftime('%Y-%m-%d')}"
    gmail_result = draft_email(
        to=GMAIL_RECIPIENT,
        subject=subject,
        body=pulse_plain,
    )

    # Create output directory
    PHASE4_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Prepare output
    output = {
        "run_at": datetime.now().isoformat(),
        "config": {
            "google_doc_id": GOOGLE_DOC_ID,
            "gmail_recipient": GMAIL_RECIPIENT,
            "phase3_input": str(PHASE3_OUTPUT),
        },
        "delivery": {
            "google_docs": docs_result,
            "gmail": gmail_result,
        },
    }

    # Write output
    PHASE4_OUTPUT_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Print summary
    print()
    print("=" * 60)
    print("  PHASE 4 — DELIVERY RESULTS")
    print("=" * 60)
    print(f"  Google Doc ID: {GOOGLE_DOC_ID}")
    print(f"  Google Docs: {docs_result['success']}")
    print(f"  Doc URL: {docs_result['doc_url']}")
    print()
    print(f"  Gmail recipient: {GMAIL_RECIPIENT}")
    print(f"  Gmail: {gmail_result['success']}")
    print()
    print(f"  Output saved -> {PHASE4_OUTPUT_FILE}")
    print("=" * 60)
    print("  Phase 4 complete. Pulse delivered.")
    print("=" * 60)
    print()

    logger.info("Phase 4 complete. Results written to %s", PHASE4_OUTPUT_FILE)


if __name__ == "__main__":
    main()
