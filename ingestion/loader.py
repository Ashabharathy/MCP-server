"""
loader.py — Main public entry point for the Phase 1 ingestion module.

Usage:
    # Google Play Store only (Phase 1 default):
    from ingestion.loader import load_playstore_reviews
    reviews = load_playstore_reviews(playstore_path="path/to/playstore.csv", weeks=12)

    # Both stores (legacy / Phase 2+):
    from ingestion.loader import load_reviews
    reviews = load_reviews(
        appstore_path="path/to/appstore.csv",
        playstore_path="path/to/playstore.csv",
        weeks=8,
    )

Both functions orchestrate the full ingestion pipeline:
  parse → filter by date → deduplicate → PII guard → return
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from ingestion.filters import apply_all_filters
from ingestion.parsers import parse_appstore_csv, parse_playstore_csv
from ingestion.schema import Review

logger = logging.getLogger(__name__)


def load_playstore_reviews(
    playstore_path: Union[str, Path],
    weeks: int = 12,
    reference_date: Optional[datetime] = None,
) -> List[Review]:
    """
    Load, normalize, filter, and deduplicate Google Play Store reviews only.

    This is the primary entry point for Phase 1, which ingests exclusively
    Google Play Store data for an 8–12 week look-back window.

    Args:
        playstore_path : Path to the Google Play Console CSV export. Required.
        weeks          : Look-back window in weeks (8–12 per spec, default 12).
                         Accepts any value 1–52.
        reference_date : Anchor date for the look-back window. Defaults to
                         datetime.utcnow(). Pass a fixed date for deterministic
                         testing.

    Returns:
        List of normalized, filtered, deduplicated Review objects sourced
        exclusively from the Google Play Store.
        Returns an empty list if no valid reviews are found — does NOT raise.

    Raises:
        FileNotFoundError: If playstore_path does not exist.
    """
    path = Path(playstore_path)
    if not path.exists():
        raise FileNotFoundError(f"Play Store CSV not found: {path}")

    logger.info("Parsing Play Store CSV (Play Store-only mode): %s", path)
    raw = parse_playstore_csv(path)
    logger.info("Total raw Play Store reviews loaded: %d", len(raw))

    filtered = apply_all_filters(raw, weeks=weeks, reference_date=reference_date)

    if not filtered:
        logger.warning(
            "load_playstore_reviews: no reviews remain after filtering "
            "(weeks=%d, total_raw=%d). Returning empty list.",
            weeks,
            len(raw),
        )

    return filtered


def load_reviews(
    appstore_path: Optional[Union[str, Path]] = None,
    playstore_path: Optional[Union[str, Path]] = None,
    weeks: int = 8,
    reference_date: Optional[datetime] = None,
) -> List[Review]:
    """
    Load, normalize, filter, and deduplicate reviews from one or both stores.

    At least one of appstore_path or playstore_path must be provided.
    Both can be provided — results are merged before filtering.

    Args:
        appstore_path  : Path to App Store Connect CSV export. Optional.
        playstore_path : Path to Google Play Console CSV export. Optional.
        weeks          : Look-back window in weeks. Default 8; max supported is 12.
        reference_date : Anchor date for the date filter. Defaults to utcnow().
                         Provided to allow deterministic testing.

    Returns:
        List of normalized, filtered, deduplicated Review objects.
        Returns an empty list if no valid reviews are found — does NOT raise.

    Raises:
        ValueError: If neither path is provided.
        FileNotFoundError: If a provided path does not exist.
    """
    if appstore_path is None and playstore_path is None:
        raise ValueError("At least one of appstore_path or playstore_path must be provided.")

    all_reviews: List[Review] = []

    if appstore_path is not None:
        path = Path(appstore_path)
        if not path.exists():
            raise FileNotFoundError(f"App Store CSV not found: {path}")
        logger.info("Parsing App Store CSV: %s", path)
        all_reviews.extend(parse_appstore_csv(path))

    if playstore_path is not None:
        path = Path(playstore_path)
        if not path.exists():
            raise FileNotFoundError(f"Play Store CSV not found: {path}")
        logger.info("Parsing Play Store CSV: %s", path)
        all_reviews.extend(parse_playstore_csv(path))

    logger.info("Total raw reviews loaded (both sources): %d", len(all_reviews))

    filtered = apply_all_filters(all_reviews, weeks=weeks, reference_date=reference_date)

    if not filtered:
        logger.warning(
            "load_reviews: no reviews remain after filtering "
            "(weeks=%d, total_raw=%d). Returning empty list.",
            weeks,
            len(all_reviews),
        )

    return filtered
