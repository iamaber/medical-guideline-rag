"""Text summarization using the unified LLM client.

This module provides synchronous and asynchronous text summarization
using the configured LLM provider.
"""

from src.services.llm_client import Generation, get_llm_client


class SummaryUnavailableError(RuntimeError):
    pass


def _summary_text(generation: Generation) -> str:
    if not generation.from_llm:
        raise SummaryUnavailableError(generation.text)
    return generation.text


def _prompt(text: str, max_words: int) -> str:
    return f"Summarize in {max_words} words:\n{text}"


def summarizer(text: str, max_words: int = 500) -> str:
    """Summarize text using the configured LLM provider (synchronous).

    Raises SummaryUnavailableError when the model could not produce a summary.
    """
    return _summary_text(get_llm_client().generate_text_sync(_prompt(text, max_words)))


async def summarizer_async(text: str, max_words: int = 500) -> str:
    """Summarize text using the configured LLM provider (asynchronous).

    Raises SummaryUnavailableError when the model could not produce a summary.
    """
    return _summary_text(await get_llm_client().generate_text(_prompt(text, max_words)))
