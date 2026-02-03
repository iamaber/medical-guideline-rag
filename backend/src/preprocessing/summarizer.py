"""Text summarization using the unified LLM client.

This module provides synchronous and asynchronous text summarization
using the configured LLM provider.
"""

from src.services.llm_client import get_llm_client


def summarizer(text: str, max_words: int = 500) -> str:
    """Summarize text using the configured LLM provider (synchronous).

    Args:
        text: The text to summarize.
        max_words: Target word count for the summary (default: 500).

    Returns:
        The summarized text.
    """
    client = get_llm_client()
    prompt = f"Summarize in {max_words} words:\n{text}"
    return client.generate_text_sync(prompt)


async def summarizer_async(text: str, max_words: int = 500) -> str:
    """Summarize text using the configured LLM provider (asynchronous).

    Args:
        text: The text to summarize.
        max_words: Target word count for the summary (default: 500).

    Returns:
        The summarized text.
    """
    client = get_llm_client()
    prompt = f"Summarize in {max_words} words:\n{text}"
    return await client.generate_text(prompt)
