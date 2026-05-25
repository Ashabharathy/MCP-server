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

import regex

from ingestion.schema import Review, fingerprint

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase 1 Normalization & Filtering Rules
# ---------------------------------------------------------------------------

_COMMON_ENGLISH_WORDS = {
    # Pronouns
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "mine", "yours", "ours", "theirs",
    "myself", "yourself", "himself", "herself", "itself", "ourselves", "themselves",
    # Determiners & Articles
    "the", "a", "an", "this", "that", "these", "those", "each", "every", "either",
    "neither", "some", "any", "no", "both", "all", "half", "many", "much", "few",
    "several", "another", "other",
    # Prepositions
    "of", "to", "in", "for", "on", "with", "at", "by", "from", "up", "about", "into",
    "over", "after", "before", "under", "between", "through", "out", "against", "during",
    "without", "towards", "upon", "concerning",
    # Conjunctions
    "and", "but", "or", "so", "because", "if", "when", "while", "as", "than", "until",
    "although", "though", "since", "unless",
    # Helper Verbs / Common Verbs
    "be", "am", "is", "are", "was", "were", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "can", "could", "will", "would", "shall",
    "should", "may", "might", "must", "say", "says", "said", "go", "goes", "went", "gone",
    "make", "makes", "made", "get", "gets", "got", "take", "takes", "took", "taken",
    "know", "knows", "knew", "known", "see", "sees", "saw", "seen", "think", "thinks", "thought",
    "come", "comes", "came", "give", "gives", "gave", "given", "want", "wants", "wanted",
    # App & Domain Specific (finance, investing, reviews)
    "app", "application", "good", "best", "great", "nice", "love", "bad", "slow", "fast",
    "update", "working", "user", "service", "customer", "support", "easy", "simple",
    "money", "invest", "investment", "investing", "mutual", "fund", "funds", "withdraw",
    "withdrawal", "deposit", "payment", "bank", "account", "kyc", "otp", "charges", "charge",
    "free", "stock", "stocks", "portfolio", "sip", "groww", "broker", "investor", "finance"
}


def remove_emojis(text: str) -> str:
    """Remove emojis and extended pictographic symbols from text."""
    if not text:
        return ""
    # Remove emojis using regex (including flags and modifiers)
    # \p{Emoji_Presentation} and \p{Extended_Pictographic} match modern emojis accurately.
    cleaned = regex.sub(r'[\p{Emoji_Presentation}\p{Extended_Pictographic}]', '', text)
    # Collapse multiple spaces resulting from removals
    return " ".join(cleaned.split())


def is_english(text: str) -> bool:
    """
    Heuristically detect if text is English.
    Returns True if at least 2 unique words match a list of common English words.
    """
    if not text:
        return False
    # Split text into lowercase alphabetical words
    words = regex.findall(r'[a-zA-Z]+', text.lower())
    if not words:
        return False
    # Count matching common English words
    eng_matches = sum(1 for w in set(words) if w in _COMMON_ENGLISH_WORDS)
    return eng_matches >= 2


def validate_review(review: Review) -> tuple[bool, Optional[str]]:
    """
    Validate a single review against expected schema constraints.

    Args:
        review: Review object to validate.

    Returns:
        Tuple of (is_valid, error_message). If is_valid is True, error_message is None.
    """
    # Validate rating (must be 1-5)
    if not isinstance(review.rating, int) or not (1 <= review.rating <= 5):
        return False, f"Invalid rating: {review.rating} (must be 1-5)"

    # Validate date (must not be None)
    if review.date is None:
        return False, "Date is None"

    # Validate text length (max 5000 characters to prevent abuse)
    if review.text and len(review.text) > 5000:
        logger.warning("Review id=%s text too long (%d chars), truncating", review.id, len(review.text))
        review.text = review.text[:5000]

    # Validate title length (max 200 characters)
    if review.title and len(review.title) > 200:
        logger.warning("Review id=%s title too long (%d chars), truncating", review.id, len(review.title))
        review.title = review.title[:200]

    # Validate source (must be 'playstore' or 'appstore')
    if review.source not in ['playstore', 'appstore']:
        return False, f"Invalid source: {review.source}"

    return True, None


def normalize_and_filter_reviews(reviews: List[Review], min_word_count: int = 6) -> List[Review]:
    """
    Normalize reviews by removing emojis, and filter based on:
    1. Schema validation (rating, date, text length, source)
    2. Minimum word count (text must have >= min_word_count words).
    3. English language check (heuristic stopword count).
    """
    filtered: List[Review] = []
    validation_errors = 0

    for r in reviews:
        # Validate schema
        is_valid, error_msg = validate_review(r)
        if not is_valid:
            logger.warning("Review id=%s validation failed: %s", r.id, error_msg)
            validation_errors += 1
            continue

        # Normalize fields (remove emojis)
        r.title = remove_emojis(r.title)
        r.text = remove_emojis(r.text)

        # Check word count (based on split of normalized text)
        words = r.text.split()
        if len(words) < min_word_count:
            logger.info("Review id=%s skipped: word count %d < %d", r.id, len(words), min_word_count)
            continue

        # Check if English
        if not is_english(r.text):
            logger.info("Review id=%s skipped: non-English language", r.id)
            continue

        filtered.append(r)

    if validation_errors > 0:
        logger.warning("Filtered %d reviews due to validation errors", validation_errors)

    return filtered





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
      2. Normalization (emoji removal) + content filtering (word count, English language)
      3. Deduplication
      4. PII field guard

    Args:
        reviews       : Raw list of Review objects from the parsers.
        weeks         : Look-back window in weeks (default 8).
        reference_date: Anchor date for the look-back window (default: utcnow).

    Returns:
        Clean, normalized, deduplicated list of Review objects within the date window.
        Reviews with fewer than 6 words, containing only emojis, or in a non-English
        language are excluded.
    """
    dated = filter_by_date_range(reviews, weeks=weeks, reference_date=reference_date)
    normalized = normalize_and_filter_reviews(dated)
    unique = deduplicate(normalized)
    assert_no_pii_fields(unique)

    logger.info(
        "Filter pipeline complete: %d reviews in → %d reviews out",
        len(reviews),
        len(unique),
    )
    return unique
