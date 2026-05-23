"""
run_phase1.py — Execute Phase 1: Review Ingestion pipeline.

Loads Google Play Store reviews for the configured look-back window
(default 12 weeks, configurable up to 52), applies date filtering and
deduplication, and outputs:
  1. A formatted console summary
  2. A JSON file: ingestion/output/reviews.json

Only Google Play Store reviews are ingested in Phase 1.
"""

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("phase1_runner")

# ── paths ──────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent
PLAYSTORE_CSV = ROOT / "ingestion" / "sample_data" / "playstore_sample.csv"
OUTPUT_DIR    = ROOT / "ingestion" / "output"
OUTPUT_FILE   = OUTPUT_DIR / "reviews.json"

# ── configuration ──────────────────────────────────────────────────────────
# Look-back window: 8–12 weeks per Phase 1 specification.
# Set to 12 to capture the full allowed range.
WEEKS = 12

# Reference date: use current UTC time so the window is always live.
# Override this (e.g. datetime(2025, 4, 1)) for deterministic test runs.
REF_DATE: datetime = datetime.now(timezone.utc).replace(tzinfo=None)

# ── run ────────────────────────────────────────────────────────────────────
def main() -> None:
    from ingestion.loader import load_playstore_reviews

    logger.info("=" * 60)
    logger.info("Phase 1 — Google Play Store Review Ingestion")
    logger.info("=" * 60)
    logger.info("Play Store CSV : %s", PLAYSTORE_CSV)
    logger.info("Look-back      : %d weeks (ref date: %s)", WEEKS, REF_DATE.date())

    reviews = load_playstore_reviews(
        playstore_path=PLAYSTORE_CSV,
        weeks=WEEKS,
        reference_date=REF_DATE,
    )

    if not reviews:
        logger.warning("No reviews returned. Check your CSV paths and date window.")
        sys.exit(1)

    # ── console summary ────────────────────────────────────────────────────
    ratings_dist = {i: sum(1 for r in reviews if r.rating == i) for i in range(1, 6)}
    date_min     = min(r.date for r in reviews).date()
    date_max     = max(r.date for r in reviews).date()
    cutoff_date  = (REF_DATE - timedelta(weeks=WEEKS)).date()

    print()
    print("=" * 60)
    print("  PHASE 1 — GOOGLE PLAY STORE INGESTION RESULTS")
    print("=" * 60)
    print(f"  Source                : Google Play Store only")
    print(f"  Look-back window      : {WEEKS} weeks")
    print(f"  Window start (cutoff) : {cutoff_date}")
    print(f"  Reference date        : {REF_DATE.date()}")
    print(f"  Total reviews stored  : {len(reviews)}")
    print(f"  Date range            : {date_min}  ->  {date_max}")
    print(f"  Rating distribution   : { {k: v for k, v in sorted(ratings_dist.items())} }")
    print()
    print("  Sample records (first 5):")
    print("  " + "-" * 56)
    for r in reviews[:5]:
        print(f"  [playstore] *{r.rating}  {r.date.date()}  {r.title[:45]}")
    print()

    # ── write JSON output ──────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "source": "playstore",
            "weeks": WEEKS,
            "reference_date": REF_DATE.date().isoformat(),
            "cutoff_date": str(cutoff_date),
            "playstore_csv": str(PLAYSTORE_CSV),
        },
        "summary": {
            "total": len(reviews),
            "playstore": len(reviews),
            "date_min": str(date_min),
            "date_max": str(date_max),
            "ratings_distribution": ratings_dist,
        },
        "reviews": [r.to_dict() for r in reviews],
    }

    OUTPUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  Output saved -> {OUTPUT_FILE}")
    print("=" * 60)
    print("  Phase 1 complete. Reviews ready for Phase 2 (Theme Analyzer).")
    print("=" * 60)
    print()

    logger.info("Phase 1 complete. %d reviews written to %s", len(reviews), OUTPUT_FILE)


if __name__ == "__main__":
    main()
