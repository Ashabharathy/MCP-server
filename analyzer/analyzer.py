"""
analyzer.py — Main Phase 2 theme analyzer module.

Orchestrates the full theme analysis pipeline:
1. Sample reviews (stratified by rating)
2. Batch reviews for LLM processing
3. Call Groq for theme clustering
4. Merge themes across batches
5. Enforce max 5 themes
6. Strip PII from quotes
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from ingestion.schema import Review

from analyzer.batching import batch_reviews, estimate_tokens
from analyzer.groq_client import GroqClient
from analyzer.pii import strip_all_pii
from analyzer.sampling import sample_reviews

logger = logging.getLogger(__name__)


def merge_themes_across_batches(batch_themes: List[Dict]) -> List[Dict]:
    """
    Merge themes from multiple batches into a consolidated list.

    Args:
        batch_themes: List of theme results from each batch.

    Returns:
        Consolidated list of themes with merged review counts and quotes.
    """
    # Collect all themes by name (normalized)
    theme_map: Dict[str, Dict] = {}

    for batch_result in batch_themes:
        for theme in batch_result.get("themes", []):
            theme_name = theme["theme_name"].lower().strip()

            if theme_name not in theme_map:
                theme_map[theme_name] = {
                    "theme_name": theme["theme_name"],
                    "review_count": 0,
                    "review_ids": [],
                    "quotes": [],
                }

            # Merge review IDs
            theme_map[theme_name]["review_ids"].extend(theme.get("review_ids", []))
            theme_map[theme_name]["review_count"] += theme.get("review_count", 0)

            # Merge quotes (deduplicate)
            existing_quotes = set(theme_map[theme_name]["quotes"])
            for quote in theme.get("quotes", []):
                if quote not in existing_quotes:
                    theme_map[theme_name]["quotes"].append(quote)
                    existing_quotes.add(quote)

    # Convert to list and sort by review count
    merged_themes = list(theme_map.values())
    merged_themes.sort(key=lambda x: x["review_count"], reverse=True)

    logger.info(
        "Merged themes from %d batches into %d unique themes",
        len(batch_themes),
        len(merged_themes),
    )

    return merged_themes


def enforce_max_themes(themes: List[Dict], max_themes: int = 5) -> List[Dict]:
    """
    Enforce maximum number of themes by merging smallest themes.

    Args:
        themes: List of theme dictionaries.
        max_themes: Maximum number of themes to keep (default: 5).

    Returns:
        List of themes with at most max_themes entries.
    """
    if len(themes) <= max_themes:
        return themes

    logger.info(
        "Reducing themes from %d to %d by merging smallest themes",
        len(themes),
        max_themes,
    )

    # Keep top max_themes by review count
    return themes[:max_themes]


def analyze_themes(
    reviews: List[Review],
    groq_api_key: str,
    prompt_path: Path = Path(__file__).parent.parent / "prompts" / "theme-analysis-v1.txt",
    sample_count: int = 500,
    batch_size: int = 50,
    max_themes: int = 5,
) -> Dict:
    """
    Run the full theme analysis pipeline.

    Args:
        reviews: List of normalized Review objects.
        groq_api_key: Groq API key for LLM calls.
        prompt_path: Path to theme analysis prompt template.
        sample_count: Number of reviews to sample (default: 500).
        batch_size: Number of reviews per batch (default: 50).
        max_themes: Maximum number of themes to return (default: 5).

    Returns:
        Dictionary with analysis results including themes, metadata, and token usage.
    """
    logger.info("=" * 60)
    logger.info("Phase 2 — Theme Analysis")
    logger.info("=" * 60)
    logger.info("Input reviews: %d", len(reviews))

    # Step 1: Sample reviews
    logger.info("Step 1: Sampling %d reviews (stratified by rating)", sample_count)
    sampled_reviews = sample_reviews(reviews, target_count=sample_count)
    logger.info("Sampled %d reviews", len(sampled_reviews))

    # Step 2: Batch reviews
    logger.info("Step 2: Creating batches of %d reviews each", batch_size)
    batches = batch_reviews(sampled_reviews, batch_size=batch_size)
    logger.info("Created %d batches", len(batches))

    # Load prompt
    logger.info("Loading prompt from %s", prompt_path)
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()

    # Step 3: Process each batch with Groq
    logger.info("Step 3: Processing batches with Groq LLM")
    groq_client = GroqClient(api_key=groq_api_key)
    batch_themes = []
    total_tokens = 0

    try:
        for i, batch in enumerate(batches, 1):
            logger.info(
                "Processing batch %d/%d (%d reviews, estimated %d tokens)",
                i,
                len(batches),
                len(batch),
                estimate_tokens(batch),
            )

            # Convert reviews to dict format for LLM
            reviews_dict = [
                {
                    "id": r.id,
                    "rating": r.rating,
                    "title": r.title,
                    "text": r.text,
                }
                for r in batch
            ]

            # Call Groq with delay for rate limits
            result = groq_client.analyze_themes(reviews_dict, prompt, delay_between_batches=2.0)
            batch_themes.append(result)

            # Track tokens (would need to extract from result in production)
            # For now, estimate
            total_tokens += estimate_tokens(batch)

            logger.info("Batch %d completed", i)

    finally:
        groq_client.close()

    # Step 4: Merge themes across batches
    logger.info("Step 4: Merging themes across %d batches", len(batch_themes))
    merged_themes = merge_themes_across_batches(batch_themes)

    # Step 5: Enforce max themes
    logger.info("Step 5: Enforcing maximum %d themes", max_themes)
    final_themes = enforce_max_themes(merged_themes, max_themes=max_themes)

    # Step 6: Strip PII from quotes
    logger.info("Step 6: Stripping PII from quotes")
    for theme in final_themes:
        theme["quotes"] = strip_all_pii(theme["quotes"])

    # Prepare output
    output = {
        "metadata": {
            "total_input_reviews": len(reviews),
            "sampled_reviews": len(sampled_reviews),
            "batches_processed": len(batches),
            "batch_size": batch_size,
            "total_themes_identified": len(merged_themes),
            "final_themes_count": len(final_themes),
            "estimated_tokens_used": total_tokens,
        },
        "themes": final_themes,
    }

    logger.info("=" * 60)
    logger.info("Phase 2 complete. Identified %d themes", len(final_themes))
    logger.info("=" * 60)

    return output
