"""
batching.py — Batching logic for Phase 2 LLM processing.

Splits reviews into batches to stay within Groq's token limits.
"""

import logging
from typing import List

from ingestion.schema import Review

logger = logging.getLogger(__name__)


def batch_reviews(
    reviews: List[Review],
    batch_size: int = 50,
) -> List[List[Review]]:
    """
    Split reviews into batches for LLM processing.

    Args:
        reviews: List of normalized Review objects.
        batch_size: Number of reviews per batch (default: 50).

    Returns:
        List of batches, where each batch is a list of Review objects.
    """
    batches = []
    for i in range(0, len(reviews), batch_size):
        batch = reviews[i : i + batch_size]
        batches.append(batch)
        logger.debug(
            "Created batch %d: %d reviews (indices %d-%d)",
            len(batches),
            len(batch),
            i,
            i + len(batch) - 1,
        )

    logger.info(
        "Split %d reviews into %d batches (batch_size=%d)",
        len(reviews),
        len(batches),
        batch_size,
    )

    return batches


def estimate_tokens(reviews: List[Review]) -> int:
    """
    Estimate token count for a batch of reviews.

    Rough estimate: ~1 token per 4 characters for review text,
    plus overhead for JSON structure and prompt.

    Args:
        reviews: List of Review objects.

    Returns:
        Estimated token count.
    """
    total_chars = 0
    for review in reviews:
        total_chars += len(review.title) + len(review.text)

    # Rough estimate: 1 token per 4 characters, plus 20% overhead
    estimated_tokens = int(total_chars / 4 * 1.2)
    return estimated_tokens
