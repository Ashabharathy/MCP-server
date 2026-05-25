"""
sampling.py — Stratified sampling of reviews for Phase 2 analysis.

Samples reviews from the full dataset to stay within Groq's token limits,
maintaining the original rating distribution.
"""

import logging
import random
from typing import List

from ingestion.schema import Review

logger = logging.getLogger(__name__)


def sample_reviews(
    reviews: List[Review],
    target_count: int = 500,
    random_seed: int = 42,
) -> List[Review]:
    """
    Sample reviews using stratified sampling by rating to maintain distribution.

    Args:
        reviews: Full list of normalized Review objects.
        target_count: Target number of reviews to sample (default: 500).
        random_seed: Random seed for reproducibility (default: 42).

    Returns:
        Sampled list of Review objects with maintained rating distribution.
    """
    if len(reviews) <= target_count:
        logger.info(
            "Total reviews (%d) <= target count (%d), returning all reviews",
            len(reviews),
            target_count,
        )
        return reviews

    random.seed(random_seed)

    # Group reviews by rating
    reviews_by_rating = {1: [], 2: [], 3: [], 4: [], 5: []}
    for review in reviews:
        reviews_by_rating[review.rating].append(review)

    # Calculate original distribution
    total = len(reviews)
    distribution = {
        rating: len(reviews_by_rating[rating]) / total for rating in range(1, 6)
    }

    logger.info(
        "Original rating distribution: 1-star: %.1f%%, 2-star: %.1f%%, 3-star: %.1f%%, 4-star: %.1f%%, 5-star: %.1f%%",
        distribution[1] * 100,
        distribution[2] * 100,
        distribution[3] * 100,
        distribution[4] * 100,
        distribution[5] * 100,
    )

    # Calculate target count per rating
    sampled: List[Review] = []
    remaining = target_count

    for rating in range(1, 6):
        rating_reviews = reviews_by_rating[rating]
        if not rating_reviews:
            continue

        # Calculate proportional count for this rating
        target_for_rating = int(target_count * distribution[rating])

        # Ensure we don't request more than available
        target_for_rating = min(target_for_rating, len(rating_reviews))

        # Adjust for rounding errors to ensure we hit exactly target_count
        if rating == 5:  # Last rating, take remaining
            target_for_rating = min(remaining, len(rating_reviews))

        # Sample from this rating group
        if len(rating_reviews) >= target_for_rating:
            sampled.extend(random.sample(rating_reviews, target_for_rating))
        else:
            # Not enough reviews in this group, take all
            sampled.extend(rating_reviews)
            target_for_rating = len(rating_reviews)

        remaining -= target_for_rating

    # Shuffle the final sample to mix ratings
    random.shuffle(sampled)

    logger.info(
        "Sampled %d reviews from %d total (stratified by rating)",
        len(sampled),
        total,
    )

    return sampled
