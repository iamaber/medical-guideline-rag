import asyncio
import json
import logging
from types import SimpleNamespace
from typing import Any, AsyncIterator, Dict, Optional

import httpx
import pytest
from groq import AsyncGroq
from pydantic_ai.models.groq import GroqModel

from src.models.llm_config import LLMProvider, LLMSettings
from src.services import llm_client as llm_module
from src.services.llm_client import (
    FALLBACK_RESPONSE,
    MAX_OUTPUT_TOKENS,
    MAX_PROMPT_CHARS,
    UnifiedLLMClient,
)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in LLMSettings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)


def settings(**overrides: Any) -> LLMSettings:
    return LLMSettings(_env_file=None, **overrides)


def completion(content: str = "Generated advice", finish_reason: str = "stop") -> Dict[str, Any]:
    return {
        "id": "offline-completion",
        "created": 1,
        "model": "qwen/qwen3.8-27b",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
    }


@pytest.fixture
async def transport(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[SimpleNamespace]:
    state = SimpleNamespace(requests=[], clients=[], init_kwargs=[], handler=None)

    async def handle(request: httpx.Request) -> httpx.Response:
        state.requests.append(request)
        if state.handler is not None:
            result = state.handler(request)
            if asyncio.iscoroutine(result):
                return await result
            return result
        return httpx.Response(200, json=completion())

    def create(**kwargs: Any) -> AsyncGroq:
        state.init_kwargs.append(kwargs)
        sdk = AsyncGroq(
            **kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle))
        )
        state.clients.append(sdk)
        return sdk

    monkeypatch.setattr(llm_module, "AsyncGroq", create)
    yield state
    for sdk in state.clients:
        await sdk.close()


def test_groq_qwen_defaults_and_secret_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    config = settings()
    assert config.llm_provider == LLMProvider.GROQ
    assert config.llm_model == "qwen/qwen3.8-27b"
    assert config.groq_reasoning_effort == "none"
    assert config.llm_max_tokens == 1600
    assert config.get_api_key_for_provider() is None

    monkeypatch.setenv("GROQ_API_KEY", "fake-provider-key")
    assert settings().get_api_key_for_provider() == "fake-provider-key"
    monkeypatch.setenv("LLM_API_KEY", "fake-unified-key")
    config = settings()
    assert config.get_api_key_for_provider() == "fake-unified-key"
    assert "fake-unified-key" not in repr(config)
    assert "fake-provider-key" not in repr(config)


@pytest.mark.parametrize("effort", [None, "low", ""])
@pytest.mark.parametrize("path", ["text", "system", "text_sync", "system_sync", "medication"])
async def test_all_generation_paths_send_bounded_instruct_requests(
    transport: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, effort: Optional[str], path: str
) -> None:
    if effort is not None:
        monkeypatch.setenv("GROQ_REASONING_EFFORT", effort)
    client = UnifiedLLMClient(settings(groq_api_key="offline-test-key"))
    assert isinstance(client.model, GroqModel)
    if path == "text":
        generation = await client.generate_text("hello")
    elif path == "system":
        generation = await client.generate("system instructions", "hello")
    elif path == "text_sync":
        generation = await asyncio.to_thread(client.generate_text_sync, "hello")
    elif path == "system_sync":
        generation = await asyncio.to_thread(client.generate_sync, "system instructions", "hello")
    else:
        generation = await client.generate_medication_advice(
            [{"name": "metformin", "schedule": "1+0+1"}],
            {"age": 45, "gender": "F"},
            [{"source": "https://pubmed.ncbi.nlm.nih.gov/123/", "abstract": "evidence " * 1000}],
            ["monograph " * 1000],
        )
    assert generation.from_llm
    advice = generation.text
    assert advice == "Generated advice"
    assert transport.init_kwargs == [
        {"api_key": "offline-test-key", "max_retries": 0, "timeout": 30}
    ]
    assert len(transport.requests) == 1
    request = transport.requests[0]
    body = json.loads(request.content)
    assert body["model"] == "qwen/qwen3.8-27b"
    assert body["max_tokens"] == 1600
    assert body["temperature"] == 0.3
    assert body["top_p"] == 0.8
    assert body["stream"] is False
    assert request.extensions["timeout"] == {"connect": 30, "read": 30, "write": 30, "pool": 30}
    if effort == "":
        assert "reasoning_effort" not in body
    else:
        assert body["reasoning_effort"] == (effort or "none")
    assert "reasoning_format" not in body
    assert sum(len(m["content"]) for m in body["messages"]) <= MAX_PROMPT_CHARS
    if path == "medication":
        assert "[PMID:123]" in body["messages"][-1]["content"]
        assert "700 words or fewer" in body["messages"][0]["content"]


async def test_truncated_response_logs_a_warning(
    transport: SimpleNamespace, caplog: pytest.LogCaptureFixture
) -> None:
    transport.handler = lambda request: httpx.Response(
        200, json=completion("Partial advice ending with", finish_reason="length")
    )
    client = UnifiedLLMClient(settings(groq_api_key="offline-test-key"))

    generation = await client.generate("private system instructions", "private user prompt")

    assert generation.from_llm
    assert generation.text == "Partial advice ending with"
    assert caplog.record_tuples == [
        (llm_module.__name__, logging.WARNING, "LLM response truncated at the output token limit")
    ]


@pytest.mark.parametrize(
    ("failure", "note"),
    [
        (429, "rate limit or quota"),
        (401, "could not complete"),
        (403, "could not complete"),
        (500, "could not complete"),
        ("timeout", "timed out after 30 seconds"),
        ("connection", "could not complete"),
        ("empty", "could not complete"),
    ],
)
@pytest.mark.parametrize("sync", [False, True])
async def test_failures_fall_back_once_without_leaking_secrets(
    transport: SimpleNamespace,
    caplog: pytest.LogCaptureFixture,
    failure: Any,
    note: str,
    sync: bool,
) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        if failure == "timeout":
            raise httpx.ReadTimeout("offline-test-key traceback", request=request)
        if failure == "connection":
            raise httpx.ConnectError("offline-test-key traceback", request=request)
        if failure == "empty":
            return httpx.Response(200, json=completion(""))
        return httpx.Response(
            failure,
            headers={"retry-after": "30"},
            json={"error": {"message": "offline-test-key traceback", "code": "insufficient_quota"}},
        )

    transport.handler = fail
    client = UnifiedLLMClient(settings(groq_api_key="offline-test-key"))

    if sync:
        generation = await asyncio.to_thread(client.generate_text_sync, "hello")
    else:
        generation = await client.generate_text("hello")
    assert not generation.from_llm
    advice = generation.text
    assert advice.startswith(FALLBACK_RESPONSE)
    assert note in advice
    if failure == 429:
        assert "Retry after 30 seconds." in advice
    assert len(transport.requests) == 1
    assert "offline-test-key" not in advice + caplog.text
    assert "traceback" not in (advice + caplog.text).lower()


@pytest.mark.parametrize(
    ("headers", "message", "expected"),
    [
        ({"retry-after": "Wed, 21 Oct 2030 07:28:00 GMT"}, "limit", "2030-10-21T07:28:00+00:00"),
        ({}, "Please try again in 5m27.36s.", "5m27.36s"),
        ({"retry-after": "offline-test-key"}, "limit", None),
    ],
)
async def test_retry_hints_survive_pydantic_ai_error_wrapping(
    transport: SimpleNamespace, headers: Dict[str, str], message: str, expected: Optional[str]
) -> None:
    transport.handler = lambda request: httpx.Response(
        429, headers=headers, json={"error": {"message": message}}
    )
    client = UnifiedLLMClient(settings(groq_api_key="offline-test-key"))
    advice = (await client.generate_text("hello")).text
    if expected:
        assert f"Retry after {expected}." in advice
    else:
        assert "Retry after" not in advice
    assert "offline-test-key" not in advice
    assert len(transport.requests) == 1


async def test_whole_call_deadline_cancels_slow_transport(
    transport: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    cancelled = asyncio.Event()

    async def slow(request: httpx.Request) -> httpx.Response:
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    transport.handler = slow
    client = UnifiedLLMClient(settings(groq_api_key="offline-test-key"))
    monkeypatch.setattr(llm_module, "LLM_TIMEOUT_SECONDS", 0.05)
    advice = (await asyncio.wait_for(client.generate_text("hello"), timeout=1)).text
    assert "timed out" in advice
    assert cancelled.is_set()
    assert len(transport.requests) == 1


async def test_prompt_and_output_caps(transport: SimpleNamespace) -> None:
    client = UnifiedLLMClient(settings(groq_api_key="offline-test-key", llm_max_tokens=9999))
    await client.generate_text("x" * MAX_PROMPT_CHARS)
    assert json.loads(transport.requests[0].content)["max_tokens"] == MAX_OUTPUT_TOKENS
    generation = await client.generate("system", "x" * MAX_PROMPT_CHARS)
    assert not generation.from_llm
    assert generation.text.startswith(FALLBACK_RESPONSE)
    assert "could not complete" in generation.text
    assert len(transport.requests) == 1


def test_existing_providers_still_initialize() -> None:
    for provider in LLMProvider:
        if provider == LLMProvider.GROQ:
            continue
        client = UnifiedLLMClient(
            settings(
                llm_provider=provider,
                llm_model="offline-test-model",
                llm_api_key="offline-test-key",
                azure_openai_endpoint="https://azure.example.test",
            )
        )
        assert client.is_available, provider
        assert "extra_body" not in client._create_agent("").model_settings


def test_health_names_groq_key_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    import app.main as main

    client = UnifiedLLMClient(settings())
    monkeypatch.setattr(main, "startup_errors", [])
    monkeypatch.setattr(
        main,
        "services",
        SimpleNamespace(
            llm_client=lambda: client,
            get_health_status=lambda: {"llm_client": False},
        ),
    )
    response = TestClient(main.app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["missing_configuration"] == ["LLM_API_KEY or GROQ_API_KEY"]
    assert "API key is missing" in client.fallback_advice
    assert "GROQ_API_KEY" in client.generate_text_sync("hello").text


async def test_api_reports_provider_failure_as_fallback(transport: SimpleNamespace) -> None:
    from app.main import _generate_advice
    from src.models.schemas import MedicationInfo, UserInput

    transport.handler = lambda request: httpx.Response(
        429, json={"error": {"message": "quota reached"}}
    )
    client = UnifiedLLMClient(settings(groq_api_key="offline-test-key"))
    advice, source = await _generate_advice(
        [MedicationInfo(name="metformin", schedule="1+0+1")],
        UserInput(meds=["metformin"], schedule=["1+0+1"], age=45, gender="F"),
        [],
        [],
        [],
        SimpleNamespace(llm_client=lambda: client),
    )
    assert source == "fallback"
    assert "rate limit or quota" in advice
    assert len(transport.requests) == 1
