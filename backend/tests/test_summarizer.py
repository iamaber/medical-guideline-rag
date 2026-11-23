from types import SimpleNamespace

import pytest

from src.preprocessing import summarizer as summarizer_module
from src.preprocessing.summarizer import SummaryUnavailableError, summarizer, summarizer_async
from src.services.llm_client import Generation


def use_client(monkeypatch: pytest.MonkeyPatch, generation: Generation) -> None:
    async def generate_text(prompt: str) -> Generation:
        return generation

    client = SimpleNamespace(
        generate_text=generate_text, generate_text_sync=lambda prompt: generation
    )
    monkeypatch.setattr(summarizer_module, "get_llm_client", lambda: client)


async def test_summaries_return_model_text(monkeypatch: pytest.MonkeyPatch) -> None:
    use_client(monkeypatch, Generation("Short summary", from_llm=True))
    assert summarizer("long text") == "Short summary"
    assert await summarizer_async("long text") == "Short summary"


async def test_fallback_notice_is_never_returned_as_a_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_client(monkeypatch, Generation("FALLBACK SAFETY NOTICE", from_llm=False))
    with pytest.raises(SummaryUnavailableError):
        summarizer("long text")
    with pytest.raises(SummaryUnavailableError):
        await summarizer_async("long text")
