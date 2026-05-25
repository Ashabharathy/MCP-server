"""
generator.py — Phase 3 pulse generation module.

Transforms themed analysis into a polished, scannable weekly pulse note
that is ≤ 250 words using Groq LLM.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List

from analyzer.groq_client import GroqClient
from analyzer.pii import strip_all_pii

logger = logging.getLogger(__name__)


def count_words(text: str) -> int:
    """
    Count words in text (simple whitespace-based count).

    Args:
        text: Input text.

    Returns:
        Word count.
    """
    return len(text.split())


def truncate_pulse(pulse_data: Dict, max_words: int = 250) -> Dict:
    """
    Truncate pulse to stay within word limit, preserving structure priority.

    Priority order: themes → quotes → action ideas (cut from bottom).

    Args:
        pulse_data: Pulse data with themes and action_ideas.
        max_words: Maximum word count (default: 250).

    Returns:
        Truncated pulse data.
    """
    # Calculate current word count
    current_words = 0

    # Count words in themes
    for theme in pulse_data["themes"]:
        current_words += count_words(theme["summary"])
        current_words += count_words(theme["quote"])

    # Count words in action ideas
    for action in pulse_data["action_ideas"]:
        current_words += count_words(action)

    if current_words <= max_words:
        return pulse_data

    logger.warning(
        "Pulse exceeds word limit: %d words (max %d). Truncating.",
        current_words,
        max_words,
    )

    # Truncate action ideas first (from bottom)
    while current_words > max_words and pulse_data["action_ideas"]:
        removed = pulse_data["action_ideas"].pop()
        current_words -= count_words(removed)
        logger.debug("Removed action idea to reduce word count")

    # If still over, truncate quotes (from bottom themes)
    theme_index = len(pulse_data["themes"]) - 1
    while current_words > max_words and theme_index >= 0:
        theme = pulse_data["themes"][theme_index]
        if theme["quote"]:
            removed = theme["quote"]
            theme["quote"] = ""
            current_words -= count_words(removed)
            logger.debug("Removed quote from theme %s", theme["theme_name"])
        theme_index -= 1

    logger.info("Truncated pulse to %d words", current_words)
    return pulse_data


def format_markdown(pulse_data: Dict) -> str:
    """
    Format pulse data as markdown.

    Args:
        pulse_data: Pulse data with themes and action_ideas.

    Returns:
        Markdown formatted string.
    """
    lines = []
    lines.append("# Weekly Review Pulse")
    lines.append("")

    lines.append("## Top Themes")
    for theme in pulse_data["themes"]:
        lines.append(f"- **{theme['theme_name']}**: {theme['summary']}")
    lines.append("")

    lines.append("## User Voices")
    for theme in pulse_data["themes"]:
        if theme["quote"]:
            lines.append(f"- {theme['quote']}")
    lines.append("")

    lines.append("## Action Ideas")
    for action in pulse_data["action_ideas"]:
        lines.append(f"- {action}")

    return "\n".join(lines)


def format_plain_text(pulse_data: Dict) -> str:
    """
    Format pulse data as plain text.

    Args:
        pulse_data: Pulse data with themes and action_ideas.

    Returns:
        Plain text formatted string.
    """
    lines = []
    lines.append("WEEKLY REVIEW PULSE")
    lines.append("=" * 40)
    lines.append("")

    lines.append("TOP THEMES")
    for theme in pulse_data["themes"]:
        lines.append(f"- {theme['theme_name']}: {theme['summary']}")
    lines.append("")

    lines.append("USER VOICES")
    for theme in pulse_data["themes"]:
        if theme["quote"]:
            lines.append(f"- {theme['quote']}")
    lines.append("")

    lines.append("ACTION IDEAS")
    for action in pulse_data["action_ideas"]:
        lines.append(f"- {action}")

    return "\n".join(lines)


def generate_pulse(
    themes: List[Dict],
    groq_api_key: str,
    prompt_path: Path = Path(__file__).parent.parent / "prompts" / "pulse-generation-v1.txt",
    max_words: int = 250,
    max_retries: int = 2,
) -> Dict:
    """
    Generate a weekly pulse from themed analysis.

    Args:
        themes: List of theme dictionaries from Phase 2.
        groq_api_key: Groq API key for LLM calls.
        prompt_path: Path to pulse generation prompt template.
        max_words: Maximum word count (default: 250).
        max_retries: Maximum retries for word count enforcement (default: 2).

    Returns:
        Dictionary with pulse data in multiple formats.
    """
    logger.info("=" * 60)
    logger.info("Phase 3 — Pulse Generation")
    logger.info("=" * 60)
    logger.info("Input themes: %d", len(themes))

    # Select top 3 themes
    top_themes = themes[:3]
    logger.info("Selected top 3 themes for pulse generation")

    # Load prompt
    logger.info("Loading prompt from %s", prompt_path)
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()

    # Prepare input for LLM
    themes_text = json.dumps(top_themes, indent=2, ensure_ascii=False)

    # Initialize Groq client
    groq_client = GroqClient(api_key=groq_api_key)

    try:
        # Generate pulse with retries for word count
        for attempt in range(max_retries + 1):
            logger.info(
                "Generation attempt %d/%d", attempt + 1, max_retries + 1
            )

            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Generate a weekly pulse from these themes:\n\n{themes_text}",
                },
            ]

            if attempt > 0:
                messages[1]["content"] += f"\n\nIMPORTANT: Your previous response was {count_words(messages[1]['content'])} words. You MUST stay under {max_words} words. Be more concise."

            response = groq_client.client.post(
                "/chat/completions",
                json={
                    "model": groq_client.model,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
            )

            response.raise_for_status()
            result = response.json()

            # Extract content
            content = result["choices"][0]["message"]["content"]
            pulse_data = json.loads(content)

            # Check word count
            pulse_text = format_plain_text(pulse_data)
            word_count = count_words(pulse_text)

            logger.info("Generated pulse: %d words", word_count)

            if word_count <= max_words:
                logger.info("Word count within limit")
                break
            else:
                logger.warning(
                    "Word count exceeds limit: %d > %d", word_count, max_words
                )
                if attempt == max_retries:
                    logger.info("Max retries reached, truncating pulse")
                    pulse_data = truncate_pulse(pulse_data, max_words)
                else:
                    logger.info("Retrying with stricter constraint")

        # Final PII check
        logger.info("Applying final PII check")
        for theme in pulse_data["themes"]:
            if theme["quote"]:
                theme["quote"] = strip_all_pii([theme["quote"]])[0]

        # Format outputs
        markdown = format_markdown(pulse_data)
        plain_text = format_plain_text(pulse_data)
        final_word_count = count_words(plain_text)

        output = {
            "metadata": {
                "input_themes_count": len(themes),
                "themes_used": len(top_themes),
                "word_count": final_word_count,
                "max_words": max_words,
                "generation_attempts": attempt + 1,
            },
            "pulse_data": pulse_data,
            "formats": {
                "markdown": markdown,
                "plain_text": plain_text,
                "json": pulse_data,
            },
        }

        logger.info("=" * 60)
        logger.info("Phase 3 complete. Pulse generated: %d words", final_word_count)
        logger.info("=" * 60)

        return output

    finally:
        groq_client.close()
