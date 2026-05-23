"""
parsers.py — CSV parsers for App Store Connect and Google Play Console exports.

Each parser reads a raw CSV file and produces a list of Review objects
using the unified schema defined in schema.py.

App Store Connect CSV fields (relevant subset):
    Rating, Title, Review, Date, App Version, Territory

Google Play Console CSV fields (relevant subset):
    Star Rating, Review Title, Review Text, Review Submit Date and Time,
    Review URL, Developer Reply Text, App Version Code
"""

import csv
import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Union

from ingestion.schema import Review, ReviewSource, fingerprint

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Date parsing helpers
# ---------------------------------------------------------------------------

_APPSTORE_DATE_FORMATS = [
    "%b %d, %Y",       # Jan 15, 2025
    "%Y-%m-%d",        # 2025-01-15
    "%d/%m/%Y",        # 15/01/2025
    "%m/%d/%Y",        # 01/15/2025
]

_PLAYSTORE_DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",   # 2025-01-15 08:30:00 UTC
    "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601
    "%b %d, %Y",           # Jan 15, 2025
    "%Y-%m-%d",            # 2025-01-15
]


def _parse_date(raw: str, formats: list) -> datetime:
    """
    Try each format in sequence. Strips common suffixes like ' UTC'.
    Raises ValueError if none match.
    """
    raw = raw.strip().replace(" UTC", "").replace("Z", "")
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: '{raw}'")


def _safe_int_rating(raw: str, source: str) -> int:
    """Parse rating string to int 1–5. Raises ValueError on bad input."""
    try:
        val = int(float(raw.strip()))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid rating '{raw}' from {source}")
    if not (1 <= val <= 5):
        raise ValueError(f"Rating out of range: {val} from {source}")
    return val


def _sanitize_text(text: str) -> str:
    """Normalize encoding: encode to UTF-8, decode with replacement for bad bytes."""
    if isinstance(text, bytes):
        return text.decode("utf-8", errors="replace")
    return text.encode("utf-8", errors="replace").decode("utf-8")


# ---------------------------------------------------------------------------
# App Store Connect parser
# ---------------------------------------------------------------------------

# Mapping of known App Store CSV column name variants → canonical names
_APPSTORE_COLUMN_MAP = {
    # Rating
    "rating": "rating",
    "star rating": "rating",
    # Title
    "title": "title",
    "review title": "title",
    # Text / body
    "review": "text",
    "body": "text",
    "review text": "text",
    "review body": "text",
    # Date
    "date": "date",
    "review date": "date",
    "updated": "date",
    # ID (optional — not always present)
    "id": "id",
    "review id": "id",
}


def parse_appstore_csv(source: Union[str, Path, io.StringIO]) -> List[Review]:
    """
    Parse an App Store Connect CSV export into normalized Review objects.

    Args:
        source: File path (str or Path) or a StringIO object (for testing).

    Returns:
        List of Review objects. Rows that cannot be parsed are skipped with a warning.
    """
    reviews: List[Review] = []

    if isinstance(source, (str, Path)):
        raw_text = Path(source).read_text(encoding="utf-8", errors="replace")
    else:
        raw_text = source.getvalue() if hasattr(source, "getvalue") else source.read()

    reader = csv.DictReader(io.StringIO(raw_text))

    if reader.fieldnames is None:
        logger.warning("App Store CSV has no headers — returning empty list")
        return []

    # Build a normalised column → original header mapping
    col_map: dict = {}
    for original_header in reader.fieldnames:
        normalised = original_header.strip().lower()
        if normalised in _APPSTORE_COLUMN_MAP:
            col_map[_APPSTORE_COLUMN_MAP[normalised]] = original_header

    for row_num, row in enumerate(reader, start=2):  # row 1 is header
        try:
            rating_raw = row.get(col_map.get("rating", ""), "").strip()
            title_raw = _sanitize_text(row.get(col_map.get("title", ""), "") or "")
            text_raw = _sanitize_text(row.get(col_map.get("text", ""), "") or "")
            date_raw = row.get(col_map.get("date", ""), "").strip()

            # Skip rows with no text body
            if not text_raw.strip():
                logger.debug("Row %d: empty review text — skipping", row_num)
                continue

            rating = _safe_int_rating(rating_raw, f"appstore row {row_num}")
            date = _parse_date(date_raw, _APPSTORE_DATE_FORMATS)

            # Use provided ID if available; otherwise fingerprint
            raw_id = row.get(col_map.get("id", ""), "").strip()
            review_id = raw_id if raw_id else fingerprint(rating, title_raw, text_raw, date)

            reviews.append(
                Review(
                    id=review_id,
                    rating=rating,
                    title=title_raw,
                    text=text_raw,
                    date=date,
                    source="appstore",
                )
            )

        except (ValueError, KeyError) as exc:
            logger.warning("App Store CSV row %d skipped: %s", row_num, exc)
            continue

    logger.info("App Store parser: %d valid reviews loaded", len(reviews))
    return reviews


# ---------------------------------------------------------------------------
# Google Play Console parser
# ---------------------------------------------------------------------------

_PLAYSTORE_COLUMN_MAP = {
    # Rating
    "star rating": "rating",
    "rating": "rating",
    # Title
    "review title": "title",
    "title": "title",
    # Text
    "review text": "text",
    "review": "text",
    "body": "text",
    # Date
    "review submit date and time": "date",
    "date": "date",
    "submitted at": "date",
    # URL (used as ID if present)
    "review url": "id",
    "review link": "id",
    "id": "id",
}


def parse_playstore_csv(source: Union[str, Path, io.StringIO]) -> List[Review]:
    """
    Parse a Google Play Console CSV export into normalized Review objects.

    Args:
        source: File path (str or Path) or a StringIO object (for testing).

    Returns:
        List of Review objects. Rows that cannot be parsed are skipped with a warning.
    """
    reviews: List[Review] = []

    if isinstance(source, (str, Path)):
        raw_text = Path(source).read_text(encoding="utf-8", errors="replace")
    else:
        raw_text = source.getvalue() if hasattr(source, "getvalue") else source.read()

    reader = csv.DictReader(io.StringIO(raw_text))

    if reader.fieldnames is None:
        logger.warning("Play Store CSV has no headers — returning empty list")
        return []

    col_map: dict = {}
    for original_header in reader.fieldnames:
        normalised = original_header.strip().lower()
        if normalised in _PLAYSTORE_COLUMN_MAP:
            col_map[_PLAYSTORE_COLUMN_MAP[normalised]] = original_header

    for row_num, row in enumerate(reader, start=2):
        try:
            rating_raw = row.get(col_map.get("rating", ""), "").strip()
            title_raw = _sanitize_text(row.get(col_map.get("title", ""), "") or "")
            text_raw = _sanitize_text(row.get(col_map.get("text", ""), "") or "")
            date_raw = row.get(col_map.get("date", ""), "").strip()

            if not text_raw.strip():
                logger.debug("Row %d: empty review text — skipping", row_num)
                continue

            rating = _safe_int_rating(rating_raw, f"playstore row {row_num}")
            date = _parse_date(date_raw, _PLAYSTORE_DATE_FORMATS)

            raw_id = row.get(col_map.get("id", ""), "").strip()
            review_id = raw_id if raw_id else fingerprint(rating, title_raw, text_raw, date)

            reviews.append(
                Review(
                    id=review_id,
                    rating=rating,
                    title=title_raw,
                    text=text_raw,
                    date=date,
                    source="playstore",
                )
            )

        except (ValueError, KeyError) as exc:
            logger.warning("Play Store CSV row %d skipped: %s", row_num, exc)
            continue

    logger.info("Play Store parser: %d valid reviews loaded", len(reviews))
    return reviews
