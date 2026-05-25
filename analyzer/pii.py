"""
pii.py — PII stripping logic for Phase 2.

Two-pass PII removal: regex for structured PII + LLM pass for contextual PII.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


# Regex patterns for structured PII
_PII_PATTERNS = [
    # Email addresses
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    # Phone numbers (various formats)
    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    r'\b\+?\d{1,3}[-.]?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
    # Numeric IDs (like Aadhaar, PAN patterns)
    r'\b\d{12}\b',  # Aadhaar-like
    r'\b[A-Z]{5}\d{4}[A-Z]\b',  # PAN-like
    # Credit card patterns
    r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    # URLs with personal info
    r'https?://[^\s]+',
]


def strip_structured_pii(text: str) -> str:
    """
    Remove structured PII using regex patterns.

    Args:
        text: Input text that may contain PII.

    Returns:
        Text with structured PII replaced with [REDACTED].
    """
    cleaned = text
    for pattern in _PII_PATTERNS:
        cleaned = re.sub(pattern, '[REDACTED]', cleaned, flags=re.IGNORECASE)

    if cleaned != text:
        logger.debug("Structured PII detected and redacted")

    return cleaned


def strip_pii_from_quotes(quotes: List[str]) -> List[str]:
    """
    Strip structured PII from a list of quotes.

    Args:
        quotes: List of quote strings.

    Returns:
        List of quotes with structured PII removed.
    """
    cleaned_quotes = []
    for quote in quotes:
        cleaned = strip_structured_pii(quote)
        cleaned_quotes.append(cleaned)

    redacted_count = sum(1 for orig, clean in zip(quotes, cleaned_quotes) if orig != clean)
    if redacted_count > 0:
        logger.info("Redacted structured PII from %d quotes", redacted_count)

    return cleaned_quotes


def strip_contextual_pii(text: str, llm_client=None) -> str:
    """
    Remove contextual PII using LLM (names, locations, etc.).

    This is a placeholder for the LLM-based PII stripping.
    In the full implementation, this would call Groq to identify
    and remove contextual PII like names, locations, etc.

    Args:
        text: Input text that may contain contextual PII.
        llm_client: LLM client for PII detection (optional).

    Returns:
        Text with contextual PII removed.
    """
    # For now, return the text as-is
    # In production, this would call the LLM to detect contextual PII
    # Example: "I, Ramesh from Delhi..." -> "I, [NAME] from [LOCATION]..."
    return text


def strip_all_pii(quotes: List[str], llm_client=None) -> List[str]:
    """
    Two-pass PII stripping: regex + LLM.

    Args:
        quotes: List of quote strings.
        llm_client: LLM client for contextual PII detection (optional).

    Returns:
        List of quotes with all PII removed.
    """
    # Pass 1: Structured PII via regex
    after_pass1 = strip_pii_from_quotes(quotes)

    # Pass 2: Contextual PII via LLM (placeholder)
    after_pass2 = [strip_contextual_pii(quote, llm_client) for quote in after_pass1]

    return after_pass2
