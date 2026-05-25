"""
run_phase3.py — Execute Phase 3: Pulse Generation pipeline.

Loads themes from Phase 2 output and uses Groq LLM to generate
a concise weekly pulse note (≤ 250 words).
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
logger = logging.getLogger("phase3_runner")

# ── paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
PHASE2_OUTPUT = ROOT / "analyzer" / "output" / "themes.json"
PHASE3_OUTPUT_DIR = ROOT / "generator" / "output"
PHASE3_OUTPUT_FILE = PHASE3_OUTPUT_DIR / "pulse.json"

# ── configuration ──────────────────────────────────────────────────────────
MAX_WORDS = 250
MAX_RETRIES = 2


def main() -> None:
    # Check for Groq API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        logger.error(
            "GROQ_API_KEY environment variable not set. "
            "Please set it before running Phase 3."
        )
        sys.exit(1)

    # Check if Phase 2 output exists
    if not PHASE2_OUTPUT.exists():
        logger.error(
            "Phase 2 output not found: %s. Please run Phase 2 first.",
            PHASE2_OUTPUT,
        )
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Phase 3 — Pulse Generation with Groq")
    logger.info("=" * 60)
    logger.info("Phase 2 output: %s", PHASE2_OUTPUT)
    logger.info("Max words: %d", MAX_WORDS)
    logger.info("Max retries: %d", MAX_RETRIES)

    # Load Phase 2 output
    logger.info("Loading themes from Phase 2 output...")
    with open(PHASE2_OUTPUT, "r", encoding="utf-8") as f:
        phase2_data = json.load(f)

    themes = phase2_data["analysis"]["themes"]
    logger.info("Loaded %d themes from Phase 2", len(themes))

    # Run pulse generation
    from generator.generator import generate_pulse

    logger.info("Starting pulse generation...")
    result = generate_pulse(
        themes=themes,
        groq_api_key=groq_api_key,
        max_words=MAX_WORDS,
        max_retries=MAX_RETRIES,
    )

    # Create output directory
    PHASE3_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Prepare output with Phase 2 context
    output = {
        "run_at": datetime.now().isoformat(),
        "config": {
            "max_words": MAX_WORDS,
            "max_retries": MAX_RETRIES,
            "phase2_input": str(PHASE2_OUTPUT),
        },
        "phase2_metadata": phase2_data["analysis"]["metadata"],
        "generation": result,
    }

    # Write output
    PHASE3_OUTPUT_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Print summary
    print()
    print("=" * 60)
    print("  PHASE 3 — PULSE GENERATION RESULTS")
    print("=" * 60)
    print(f"  Input themes (Phase 2): {len(themes)}")
    print(f"  Themes used: {result['metadata']['themes_used']}")
    print(f"  Word count: {result['metadata']['word_count']}")
    print(f"  Max words: {result['metadata']['max_words']}")
    print(f"  Generation attempts: {result['metadata']['generation_attempts']}")
    print()
    print("  Generated Pulse:")
    print("  " + "-" * 56)
    print(result["formats"]["plain_text"])
    print()
    print(f"  Output saved -> {PHASE3_OUTPUT_FILE}")
    print("=" * 60)
    print("  Phase 3 complete. Pulse ready for delivery.")
    print("=" * 60)
    print()

    logger.info("Phase 3 complete. Results written to %s", PHASE3_OUTPUT_FILE)


if __name__ == "__main__":
    main()
