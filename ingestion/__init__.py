"""
Phase 1 — Review Ingestion Module

Public interface:
    # Google Play Store only (Phase 1 default):
    from ingestion.loader import load_playstore_reviews

    # Both stores (legacy):
    from ingestion.loader import load_reviews
"""

from ingestion.loader import load_playstore_reviews, load_reviews

__all__ = ["load_playstore_reviews", "load_reviews"]
