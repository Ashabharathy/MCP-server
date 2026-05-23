"""
test_ingestion.py — Phase 1 test suite covering all 9 test cases from eval.md.

Test IDs map directly to eval.md Phase 1:
  P1-T1  Parse valid App Store CSV export
  P1-T2  Parse valid Play Store CSV export
  P1-T3  Apply 8-week date filter
  P1-T4  Apply 12-week date filter
  P1-T5  Duplicate reviews in input
  P1-T6  Missing fields in CSV row
  P1-T7  Non-UTF-8 encoded characters
  P1-T8  Empty CSV file
  P1-T9  0 reviews in date range

Run with:
    python -m pytest tests/test_ingestion.py -v
"""

import io
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Make sure the project root is on sys.path when running from any directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.parsers import parse_appstore_csv, parse_playstore_csv
from ingestion.filters import filter_by_date_range, deduplicate, apply_all_filters
from ingestion.schema import Review
from ingestion.loader import load_reviews

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_DIR = Path(__file__).parent.parent / "ingestion" / "sample_data"
APPSTORE_SAMPLE = SAMPLE_DIR / "appstore_sample.csv"
PLAYSTORE_SAMPLE = SAMPLE_DIR / "playstore_sample.csv"

# Reference date anchored to 2025-03-01 so sample data (Jan–Feb 2025) is within 8 weeks
REF_DATE = datetime(2025, 3, 1)


def _appstore_csv(rows: list[str]) -> io.StringIO:
    """Build a minimal App Store CSV StringIO from a list of data rows."""
    header = "Rating,Title,Review,Date,App Version,Territory"
    content = "\n".join([header] + rows)
    return io.StringIO(content)


def _playstore_csv(rows: list[str]) -> io.StringIO:
    """Build a minimal Play Store CSV StringIO from a list of data rows."""
    header = "Star Rating,Review Title,Review Text,Review Submit Date and Time,App Version Code,Developer Reply Text"
    content = "\n".join([header] + rows)
    return io.StringIO(content)


# ---------------------------------------------------------------------------
# P1-T1 — Parse valid App Store CSV export
# ---------------------------------------------------------------------------

def test_p1_t1_parse_valid_appstore_csv():
    """P1-T1: All records from appstore_sample.csv normalize to the expected schema."""
    reviews = parse_appstore_csv(APPSTORE_SAMPLE)

    assert len(reviews) > 0, "Expected at least one review from App Store sample"

    for r in reviews:
        # Schema fields present
        assert isinstance(r.id, str) and r.id, "id must be a non-empty string"
        assert isinstance(r.rating, int) and 1 <= r.rating <= 5, "rating must be int 1–5"
        assert isinstance(r.title, str), "title must be a string"
        assert isinstance(r.text, str), "text must be a string"
        assert isinstance(r.date, datetime), "date must be a datetime"
        assert r.source == "appstore", "source must be 'appstore'"

        # No PII fields
        assert not hasattr(r, "username"), "PII field 'username' must not exist"
        assert not hasattr(r, "user_id"), "PII field 'user_id' must not exist"
        assert not hasattr(r, "reviewer_name"), "PII field 'reviewer_name' must not exist"


# ---------------------------------------------------------------------------
# P1-T2 — Parse valid Play Store CSV export
# ---------------------------------------------------------------------------

def test_p1_t2_parse_valid_playstore_csv():
    """P1-T2: All records from playstore_sample.csv normalize to the expected schema."""
    reviews = parse_playstore_csv(PLAYSTORE_SAMPLE)

    assert len(reviews) > 0, "Expected at least one review from Play Store sample"

    for r in reviews:
        assert isinstance(r.id, str) and r.id
        assert isinstance(r.rating, int) and 1 <= r.rating <= 5
        assert isinstance(r.title, str)
        assert isinstance(r.text, str)
        assert isinstance(r.date, datetime)
        assert r.source == "playstore"

        assert not hasattr(r, "username")
        assert not hasattr(r, "user_id")
        assert not hasattr(r, "reviewer_name")


# ---------------------------------------------------------------------------
# P1-T3 — Apply 8-week date filter
# ---------------------------------------------------------------------------

def test_p1_t3_eight_week_filter():
    """P1-T3: Only reviews within the last 8 weeks relative to REF_DATE are returned."""
    reviews = parse_appstore_csv(APPSTORE_SAMPLE)
    filtered = filter_by_date_range(reviews, weeks=8, reference_date=REF_DATE)

    cutoff = REF_DATE - timedelta(weeks=8)
    for r in filtered:
        assert r.date >= cutoff, f"Review date {r.date} is before 8-week cutoff {cutoff}"


# ---------------------------------------------------------------------------
# P1-T4 — Apply 12-week date filter
# ---------------------------------------------------------------------------

def test_p1_t4_twelve_week_filter():
    """P1-T4: Only reviews within the last 12 weeks relative to REF_DATE are returned."""
    reviews = parse_appstore_csv(APPSTORE_SAMPLE)
    filtered_8 = filter_by_date_range(reviews, weeks=8, reference_date=REF_DATE)
    filtered_12 = filter_by_date_range(reviews, weeks=12, reference_date=REF_DATE)

    # 12-week window must return >= results than 8-week
    assert len(filtered_12) >= len(filtered_8), (
        "12-week filter should return at least as many reviews as 8-week filter"
    )

    cutoff = REF_DATE - timedelta(weeks=12)
    for r in filtered_12:
        assert r.date >= cutoff, f"Review date {r.date} is before 12-week cutoff {cutoff}"


# ---------------------------------------------------------------------------
# P1-T5 — Duplicate reviews in input
# ---------------------------------------------------------------------------

def test_p1_t5_deduplication():
    """P1-T5: Duplicate reviews are removed; unique set returned."""
    rows = [
        '5,Great app,This app is excellent for investing.,2025-01-10,5.2.0,IN',
        '5,Great app,This app is excellent for investing.,2025-01-10,5.2.0,IN',  # exact duplicate
        '4,Decent,Good but could be better.,2025-01-11,5.2.0,IN',
    ]
    reviews = parse_appstore_csv(_appstore_csv(rows))
    unique = deduplicate(reviews)

    assert len(unique) == 2, f"Expected 2 unique reviews, got {len(unique)}"

    ids = [r.id for r in unique]
    assert len(ids) == len(set(ids)), "Duplicate IDs found after deduplication"


# ---------------------------------------------------------------------------
# P1-T6 — Missing fields in CSV row
# ---------------------------------------------------------------------------

def test_p1_t6_missing_fields_graceful():
    """P1-T6: Rows with missing required fields are skipped; no crash."""
    rows = [
        '5,Valid review,This is a valid review.,2025-01-10,5.2.0,IN',
        ',,,,,',                                      # all fields missing
        '3,No body,,2025-01-11,5.2.0,IN',            # empty review text
        '5,Missing date,Review text here,,5.2.0,IN', # missing date
    ]
    # Should not raise any exception
    reviews = parse_appstore_csv(_appstore_csv(rows))

    # Only the valid row should survive
    assert len(reviews) == 1, f"Expected 1 valid review, got {len(reviews)}"
    assert reviews[0].text == "This is a valid review."


# ---------------------------------------------------------------------------
# P1-T7 — Non-UTF-8 encoded characters
# ---------------------------------------------------------------------------

def test_p1_t7_non_utf8_characters():
    """P1-T7: Non-UTF-8 characters are handled without crash; text is sanitized."""
    # Build a CSV string with a latin-1 character that is invalid UTF-8 when re-encoded
    rows = [
        '4,Encoding test,Review with special chars caf\u00e9 and na\u00efve,2025-01-10,5.2.0,IN',
        '3,Another review,Normal ASCII text here.,2025-01-11,5.2.0,IN',
    ]
    csv_content = "Rating,Title,Review,Date,App Version,Territory\n" + "\n".join(rows)
    source = io.StringIO(csv_content)

    reviews = parse_appstore_csv(source)

    assert len(reviews) >= 1, "Expected at least one review to parse successfully"
    for r in reviews:
        # Text must be a valid Python string (UTF-8 safe)
        assert isinstance(r.text, str)
        r.text.encode("utf-8")  # must not raise


# ---------------------------------------------------------------------------
# P1-T8 — Empty CSV file
# ---------------------------------------------------------------------------

def test_p1_t8_empty_csv_appstore():
    """P1-T8 (App Store): Empty CSV returns empty list without crash."""
    source = io.StringIO("")
    reviews = parse_appstore_csv(source)
    assert reviews == [], f"Expected empty list, got {reviews}"


def test_p1_t8_empty_csv_playstore():
    """P1-T8 (Play Store): Empty CSV returns empty list without crash."""
    source = io.StringIO("")
    reviews = parse_playstore_csv(source)
    assert reviews == [], f"Expected empty list, got {reviews}"


def test_p1_t8_header_only_csv():
    """P1-T8 (header only): CSV with only a header row returns empty list."""
    source = _appstore_csv([])  # header only, no data rows
    reviews = parse_appstore_csv(source)
    assert reviews == []


# ---------------------------------------------------------------------------
# P1-T9 — 0 reviews in date range
# ---------------------------------------------------------------------------

def test_p1_t9_no_reviews_in_date_range():
    """P1-T9: If no reviews fall within the date window, returns empty list gracefully."""
    # Sample reviews are from Jan–Feb 2025.
    # Use reference_date=2025-05-01 with weeks=4:
    # cutoff = 2025-04-03 → all Jan-Feb 2025 reviews are BEFORE the cutoff → excluded.
    future_ref = datetime(2025, 5, 1)

    reviews = parse_appstore_csv(APPSTORE_SAMPLE)
    assert len(reviews) > 0, "Sample data must have reviews before filtering"

    filtered = filter_by_date_range(reviews, weeks=4, reference_date=future_ref)
    assert filtered == [], f"Expected empty list, got {len(filtered)} reviews"


def test_p1_t9_load_reviews_empty_result():
    """P1-T9 (loader): load_reviews returns empty list when nothing matches the window."""
    # Same logic: reference 2025-05-01, weeks=4 → cutoff=2025-04-03 → no Jan-Feb 2025 reviews
    future_ref = datetime(2025, 5, 1)
    result = load_reviews(
        appstore_path=APPSTORE_SAMPLE,
        weeks=4,
        reference_date=future_ref,
    )
    assert result == []


# ---------------------------------------------------------------------------
# Integration test — load_reviews end-to-end
# ---------------------------------------------------------------------------

def test_load_reviews_both_sources():
    """Integration: load_reviews merges both sources, deduplicates, and filters correctly."""
    reviews = load_reviews(
        appstore_path=APPSTORE_SAMPLE,
        playstore_path=PLAYSTORE_SAMPLE,
        weeks=8,
        reference_date=REF_DATE,
    )

    assert len(reviews) > 0

    sources = {r.source for r in reviews}
    assert "appstore" in sources, "Expected App Store reviews in merged result"
    assert "playstore" in sources, "Expected Play Store reviews in merged result"

    ids = [r.id for r in reviews]
    assert len(ids) == len(set(ids)), "Duplicate IDs found in merged result"


def test_load_reviews_raises_if_no_paths():
    """load_reviews must raise ValueError when no paths are provided."""
    with pytest.raises(ValueError, match="At least one"):
        load_reviews()


def test_load_reviews_raises_if_file_missing():
    """load_reviews must raise FileNotFoundError for a non-existent path."""
    with pytest.raises(FileNotFoundError):
        load_reviews(appstore_path="nonexistent_file.csv")


# ---------------------------------------------------------------------------
# PII field audit
# ---------------------------------------------------------------------------

def test_no_pii_fields_in_output():
    """PII field audit: no Review object from parsers carries PII attributes."""
    from ingestion.filters import assert_no_pii_fields

    reviews = load_reviews(
        appstore_path=APPSTORE_SAMPLE,
        playstore_path=PLAYSTORE_SAMPLE,
        weeks=8,
        reference_date=REF_DATE,
    )

    # Should not raise
    assert_no_pii_fields(reviews)


# ---------------------------------------------------------------------------
# load_playstore_reviews tests
# ---------------------------------------------------------------------------

def test_load_playstore_reviews_success():
    """Verify load_playstore_reviews properly ingests Play Store reviews only."""
    from ingestion.loader import load_playstore_reviews

    reviews = load_playstore_reviews(
        playstore_path=PLAYSTORE_SAMPLE,
        weeks=12,
        reference_date=REF_DATE,
    )
    assert len(reviews) > 0
    for r in reviews:
        assert r.source == "playstore"


def test_load_playstore_reviews_missing_file():
    """Verify load_playstore_reviews raises FileNotFoundError on missing file."""
    from ingestion.loader import load_playstore_reviews

    with pytest.raises(FileNotFoundError):
        load_playstore_reviews(playstore_path="nonexistent_playstore.csv")
