"""
filters.py — Post-parse filtering and deduplication for review records.

Responsibilities:
  1. Date-range filtering: keep only reviews within the configured window.
  2. Deduplication: remove duplicate records by ID or content fingerprint.
  3. PII field exclusion: ensure no reviewer usernames or user IDs remain.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from ingestion.schema import Review, fingerprint

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Date-range filter
# ---------------------------------------------------------------------------

def filter_by_date_range(
    reviews: List[Review],
    weeks: int = 8,
    reference_date: Optional[datetime] = None,
) -> List[Review]:
    """
    Keep only reviews published within the last `weeks` weeks.

    Args:
        reviews       : Input list of Review objects.
        weeks         : Number of weeks to look back. Must be 1–52.
                        Default is 8; problem statement allows up to 12.
        reference_date: The "today" anchor. Defaults to datetime.utcnow().
                        Exposed as a parameter to make the function fully
                        testable without depending on wall-clock time.

    Returns:
        Filtered list of Review objects within the date window.

    Raises:
        ValueError: If weeks is outside the valid range.
    """
    if not (1 <= weeks <= 52):
        raise ValueError(f"weeks must be between 1 and 52, got {weeks}")

    anchor = reference_date or datetime.utcnow()
    cutoff = anchor - timedelta(weeks=weeks)

    filtered = [r for r in reviews if r.date >= cutoff]

    excluded = len(reviews) - len(filtered)
    if excluded:
        logger.info(
            "Date filter (%d weeks, cutoff %s): excluded %d / %d reviews",
            weeks,
            cutoff.date().isoformat(),
            excluded,
            len(reviews),
        )

    return filtered


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate(reviews: List[Review]) -> List[Review]:
    """
    Remove duplicate Review records.

    Deduplication strategy (in priority order):
      1. If two records share the same `id`, keep the first occurrence.
      2. If two records have the same content fingerprint
         (rating + title + text + date), keep the first occurrence.

    This handles the common case of overlapping date windows producing
    duplicate exports, and the edge case where the source does not
    provide a stable ID.

    Args:
        reviews: List of Review objects (may contain duplicates).

    Returns:
        Deduplicated list preserving original order.
    """
    seen_ids: set = set()
    seen_fingerprints: set = set()
    unique: List[Review] = []

    for review in reviews:
        fp = fingerprint(review.rating, review.title, review.text, review.date)

        if review.id in seen_ids or fp in seen_fingerprints:
            logger.debug("Duplicate review skipped: id=%s fp=%s", review.id, fp)
            continue

        seen_ids.add(review.id)
        seen_fingerprints.add(fp)
        unique.append(review)

    removed = len(reviews) - len(unique)
    if removed:
        logger.info("Deduplication: removed %d duplicate(s), %d unique remain", removed, len(unique))

    return unique


# ---------------------------------------------------------------------------
# PII field guard
# ---------------------------------------------------------------------------

# Fields that must NOT appear in the normalized output.
# This is a safety check — parsers already exclude these fields.
_FORBIDDEN_PII_FIELDS = {"reviewer_name", "username", "user_id", "email", "author"}


def assert_no_pii_fields(reviews: List[Review]) -> None:
    """
    Assert that no Review object carries PII field names.

    This is a belt-and-suspenders check. The parsers should already
    exclude these fields, but this guard catches future regressions.

    Raises:
        AssertionError: If a Review object has any attribute in _FORBIDDEN_PII_FIELDS.
    """
    for review in reviews:
        for field_name in _FORBIDDEN_PII_FIELDS:
            assert not hasattr(review, field_name), (
                f"PII field '{field_name}' found on Review object (id={review.id}). "
                "Remove it from the parser output immediately."
            )


# ---------------------------------------------------------------------------
# Combined pipeline helper
# ---------------------------------------------------------------------------

def apply_all_filters(
    reviews: List[Review],
    weeks: int = 8,
    reference_date: Optional[datetime] = None,
) -> List[Review]:
    """
    Apply the full filter chain in the correct order:
      1. Date-range filter
      2. Deduplication

    Args:
        reviews       : Raw list of Review objects from the parsers.
        weeks         : Look-back window in weeks (default 8).
        reference_date: Anchor date for the look-back window (default: utcnow).

    Returns:
        Clean, deduplicated list of Review objects within the date window.
    """
    dated = filter_by_date_range(reviews, weeks=weeks, reference_date=reference_date)
    unique = deduplicate(dated)
    assert_no_pii_fields(unique)

    logger.info(
        "Filter pipeline complete: %d reviews in → %d reviews out",
        len(reviews),
        len(unique),
    )
    return unique
