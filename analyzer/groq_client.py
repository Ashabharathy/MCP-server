"""
groq_client.py — Groq LLM client for Phase 2 theme analysis.

Handles communication with Groq API for theme clustering.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for Groq Llama-3.3-70b-versatile API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",
    ):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key. If None, reads from GROQ_API_KEY env var.
            model: Model name to use (default: llama-3.3-70b-versatile).
            base_url: Groq API base URL.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key not provided. Set GROQ_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.base_url = base_url
        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )

    def analyze_themes(
        self,
        reviews: List[Dict],
        prompt: str,
        max_retries: int = 3,
        delay_between_batches: float = 2.0,
    ) -> Dict:
        """
        Call Groq to analyze themes for a batch of reviews.

        Args:
            reviews: List of review dictionaries with id, rating, title, text.
            prompt: System prompt for theme analysis.
            max_retries: Maximum number of retries on failure.

        Returns:
            Dictionary with themes from LLM response.

        Raises:
            Exception: If all retries fail.
        """
        # Format reviews for the prompt
        reviews_text = json.dumps(reviews, indent=2, ensure_ascii=False)

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Analyze these reviews and identify themes:\n\n{reviews_text}",
            },
        ]

        for attempt in range(max_retries):
            try:
                response = self.client.post(
                    "/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                        "temperature": 0.3,
                        "max_tokens": 4096,
                    },
                )

                response.raise_for_status()
                result = response.json()

                # Extract content
                content = result["choices"][0]["message"]["content"]
                themes_data = json.loads(content)

                # Log token usage
                prompt_tokens = result.get("usage", {}).get("prompt_tokens", 0)
                completion_tokens = result.get("usage", {}).get("completion_tokens", 0)
                total_tokens = result.get("usage", {}).get("total_tokens", 0)

                logger.info(
                    "Groq API call successful: %d prompt tokens, %d completion tokens, %d total tokens",
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                )

                # Add delay before next call to respect rate limits
                if delay_between_batches > 0:
                    logger.debug("Sleeping %.1f seconds before next batch", delay_between_batches)
                    time.sleep(delay_between_batches)

                return themes_data

            except httpx.HTTPStatusError as e:
                # Handle rate limit specifically
                if e.response.status_code == 429:
                    error_data = e.response.json()
                    retry_after = error_data.get("error", {}).get("message", "")
                    logger.warning(
                        "Rate limit hit (attempt %d/%d): %s",
                        attempt + 1,
                        max_retries,
                        retry_after,
                    )
                    # Extract retry time from error message if available
                    if "try again in" in retry_after:
                        try:
                            retry_seconds = float(retry_after.split("try again in")[1].split("s")[0].strip())
                            logger.info("Rate limit: waiting %.1f seconds", retry_seconds)
                            time.sleep(retry_seconds)
                        except:
                            # Default exponential backoff if parsing fails
                            backoff = min(2 ** attempt, 30)
                            logger.info("Rate limit: default backoff %.1f seconds", backoff)
                            time.sleep(backoff)
                    else:
                        # Default exponential backoff
                        backoff = min(2 ** attempt, 30)
                        logger.info("Rate limit: default backoff %.1f seconds", backoff)
                        time.sleep(backoff)
                else:
                    logger.warning(
                        "Groq API call failed (attempt %d/%d): %s",
                        attempt + 1,
                        max_retries,
                        e.response.text,
                    )
                    if attempt == max_retries - 1:
                        raise Exception(f"Groq API failed after {max_retries} retries: {e}")

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    "Failed to parse Groq response (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries,
                    e,
                )
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to parse Groq response after {max_retries} retries: {e}")

        raise Exception("Unexpected error in Groq API call")

    def close(self):
        """Close the HTTP client."""
        self.client.close()
