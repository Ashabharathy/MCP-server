"""
run_phase2.py — Execute Phase 2: Theme Analysis pipeline.

Loads reviews from Phase 1 output, samples 500 reviews, and uses Groq LLM
to identify themes and extract representative quotes.
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
logger = logging.getLogger("phase2_runner")

# ── paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
PHASE1_OUTPUT = ROOT / "ingestion" / "output" / "reviews.json"
PHASE2_OUTPUT_DIR = ROOT / "analyzer" / "output"
PHASE2_OUTPUT_FILE = PHASE2_OUTPUT_DIR / "themes.json"

# ── configuration ──────────────────────────────────────────────────────────
SAMPLE_COUNT = 500
BATCH_SIZE = 50
MAX_THEMES = 5


def main() -> None:
    # Check for Groq API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        logger.error(
            "GROQ_API_KEY environment variable not set. "
            "Please set it before running Phase 2."
        )
        sys.exit(1)

    # Check if Phase 1 output exists
    if not PHASE1_OUTPUT.exists():
        logger.error(
            "Phase 1 output not found: %s. Please run Phase 1 first.",
            PHASE1_OUTPUT,
        )
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Phase 2 — Theme Analysis with Groq")
    logger.info("=" * 60)
    logger.info("Phase 1 output: %s", PHASE1_OUTPUT)
    logger.info("Sample count: %d reviews", SAMPLE_COUNT)
    logger.info("Batch size: %d reviews", BATCH_SIZE)
    logger.info("Max themes: %d", MAX_THEMES)

    # Load Phase 1 output
    logger.info("Loading reviews from Phase 1 output...")
    with open(PHASE1_OUTPUT, "r", encoding="utf-8") as f:
        phase1_data = json.load(f)

    reviews_dict = phase1_data["reviews"]
    logger.info("Loaded %d reviews from Phase 1", len(reviews_dict))

    # Convert to Review objects
    from ingestion.schema import Review

    reviews = []
    for r_dict in reviews_dict:
        reviews.append(
            Review(
                id=r_dict["id"],
                rating=r_dict["rating"],
                title=r_dict["title"],
                text=r_dict["text"],
                date=datetime.fromisoformat(r_dict["date"]),
                source=r_dict["source"],
            )
        )

    # Run theme analysis
    from analyzer.analyzer import analyze_themes

    logger.info("Starting theme analysis...")
    result = analyze_themes(
        reviews=reviews,
        groq_api_key=groq_api_key,
        sample_count=SAMPLE_COUNT,
        batch_size=BATCH_SIZE,
        max_themes=MAX_THEMES,
    )

    # Create output directory
    PHASE2_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Prepare output with Phase 1 context
    output = {
        "run_at": datetime.now().isoformat(),
        "config": {
            "sample_count": SAMPLE_COUNT,
            "batch_size": BATCH_SIZE,
            "max_themes": MAX_THEMES,
            "phase1_input": str(PHASE1_OUTPUT),
        },
        "phase1_summary": phase1_data["summary"],
        "analysis": result,
    }

    # Write output
    PHASE2_OUTPUT_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Print summary
    print()
    print("=" * 60)
    print("  PHASE 2 — THEME ANALYSIS RESULTS")
    print("=" * 60)
    print(f"  Input reviews (Phase 1): {len(reviews)}")
    print(f"  Sampled reviews: {result['metadata']['sampled_reviews']}")
    print(f"  Batches processed: {result['metadata']['batches_processed']}")
    print(f"  Themes identified: {result['metadata']['total_themes_identified']}")
    print(f"  Final themes: {result['metadata']['final_themes_count']}")
    print(f"  Estimated tokens used: {result['metadata']['estimated_tokens_used']}")
    print()
    print("  Themes:")
    print("  " + "-" * 56)
    for i, theme in enumerate(result["themes"], 1):
        print(
            f"  {i}. {theme['theme_name']} ({theme['review_count']} reviews)"
        )
        print(f"     Quotes: {len(theme['quotes'])}")
    print()
    print(f"  Output saved -> {PHASE2_OUTPUT_FILE}")
    print("=" * 60)
    print("  Phase 2 complete. Themes ready for Phase 3 (Pulse Generation).")
    print("=" * 60)
    print()

    logger.info("Phase 2 complete. Results written to %s", PHASE2_OUTPUT_FILE)


if __name__ == "__main__":
    main()
