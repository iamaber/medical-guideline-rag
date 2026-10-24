"""LLM prompt grounding tests.

These tests never touch a provider: the model is replaced with a sentinel and
``generate_with_system_prompt`` is stubbed, so we assert on the prompt only.
"""

from src.services.llm_client import FALLBACK_RESPONSE, UnifiedLLMClient


def _client_with_stub():
    client = object.__new__(UnifiedLLMClient)
    client._model = object()

    captured = {}

    async def _capture(system_prompt: str, user_prompt: str) -> str:
        captured["system"] = system_prompt
        captured["user"] = user_prompt
        return "advice"

    client.generate_with_system_prompt = _capture
    return client, captured


async def test_retrieved_abstracts_reach_the_prompt():
    client, captured = _client_with_stub()

    advice = await client.generate_medication_advice(
        medications=[{"name": "warfarin", "schedule": "0+0+1"}],
        patient_info={"age": 70, "gender": "M", "medical_conditions": []},
        pubmed_context=[
            {
                "id": "PMID:12345678_abstract",
                "title": "Anticoagulation safety",
                "abstract": "Monitor INR closely when warfarin is co-prescribed.",
                "publication_year": 2023,
            }
        ],
        medex_context=["Warfarin interacts with aspirin, raising bleeding risk."],
    )

    assert advice == "advice"
    assert "[PMID:12345678_abstract]" in captured["user"]
    assert "Monitor INR closely" in captured["user"]
    assert "Warfarin interacts with aspirin" in captured["user"]
    assert "no matching literature" not in captured["user"]
    assert "cite" in captured["system"].lower()


async def test_missing_context_is_stated_explicitly():
    client, captured = _client_with_stub()

    await client.generate_medication_advice(
        medications=[{"name": "metformin", "schedule": "1+0+1"}],
        patient_info={"age": 40, "gender": "F"},
        pubmed_context=[],
        medex_context=[],
    )

    assert "no matching literature was retrieved" in captured["user"]
    assert "none available" in captured["user"]


def test_evidence_is_truncated_to_a_budget():
    articles = [
        {"id": f"PMID:{i}", "title": "t", "abstract": "x" * 5000, "publication_year": 2020}
        for i in range(20)
    ]
    formatted = UnifiedLLMClient._format_evidence(articles)
    assert 0 < len(formatted) <= 6000


def test_fallback_is_reported_when_no_model_is_configured():
    client = object.__new__(UnifiedLLMClient)
    client._model = None

    assert client.fallback_advice == FALLBACK_RESPONSE
    assert client.is_available is False
