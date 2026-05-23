"""
schema.py — Normalized review record definition.

All ingested reviews, regardless of source (App Store or Play Store),
are mapped into this unified schema before passing to downstream modules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


# Supported review sources
ReviewSource = Literal["appstore", "playstore"]


@dataclass
class Review:
    """
    Normalized review record.

    Fields:
        id      : Unique identifier. Derived from source-specific ID or content fingerprint.
        rating  : Integer star rating, 1–5.
        title   : Review title / headline. Empty string if not provided.
        text    : Full review body text.
        date    : Publication date (timezone-naive UTC).
        source  : Origin store: "appstore" or "playstore".
    """

    id: str
    rating: int
    title: str
    text: str
    date: datetime
    source: ReviewSource

    def __post_init__(self) -> None:
        if not (1 <= self.rating <= 5):
            raise ValueError(f"Rating must be 1–5, got {self.rating}")
        if not self.id:
            raise ValueError("Review id must not be empty")

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict representation."""
        return {
            "id": self.id,
            "rating": self.rating,
            "title": self.title,
            "text": self.text,
            "date": self.date.isoformat(),
            "source": self.source,
        }


def fingerprint(rating: int, title: str, text: str, date: datetime) -> str:
    """
    Generate a stable content-based ID for deduplication when a
    source-specific ID is unavailable.
    """
    import hashlib

    raw = f"{rating}|{title.strip().lower()}|{text.strip().lower()}|{date.date().isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
