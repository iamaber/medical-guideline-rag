"""API contract tests using a fake service container.

The FastAPI lifespan is deliberately not entered, so no embedding model is
downloaded and no outbound request is made.
"""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr

import app.main as main
from app.main import _convert_markdown_to_html_content, _enforce_access, _reset_rate_limit


class _FakeLLM:
    is_available = False
    fallback_advice = "FALLBACK SAFETY NOTICE"

    def missing_configuration(self):
        return ["LLM_API_KEY"]

    def get_model_info(self):
        return {"is_available": False}


class _FakeDrugLookup:
    def find_drug_url(self, name):
        return None


class _FakeJinaScraper:
    def scrape_medex_page(self, url):
        return None


class _FakeVectorSearch:
    def enhanced_medical_search(self, **kwargs):
        return []

    def get_stats(self):
        return {"total_documents": 0}


class _FakeKnowledgeGraph:
    def analyze_drug_interactions(self, medications):
        return []

    def get_stats(self):
        return {}


class _FakeContainer:
    def all_available(self):
        return True

    def drug_lookup(self):
        return _FakeDrugLookup()

    def jina_scraper(self):
        return _FakeJinaScraper()

    def vector_search(self):
        return _FakeVectorSearch()

    def llm_client(self):
        return _FakeLLM()

    def knowledge_graph(self):
        return _FakeKnowledgeGraph()

    def get_health_status(self):
        return {"drug_lookup": True, "llm_client": False}


@pytest.fixture()
def client():
    return TestClient(main.app)


def test_health_reports_unhealthy_when_services_are_missing(client, monkeypatch):
    monkeypatch.setattr(main, "services", None)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "unhealthy"
    assert response.json()["services"] == "unavailable"


def test_health_reports_degraded_and_lists_missing_configuration(client, monkeypatch):
    monkeypatch.setattr(main, "services", _FakeContainer())
    monkeypatch.setattr(main, "startup_errors", [])

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["missing_configuration"] == ["LLM_API_KEY"]


def test_advise_reports_fallback_source(client, monkeypatch):
    monkeypatch.setattr(main, "services", _FakeContainer())
    monkeypatch.setattr(main, "startup_errors", [])

    response = client.post(
        "/advise",
        json={"meds": ["metformin"], "schedule": ["1+0+1"], "age": 45, "gender": "F"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["advice_source"] == "fallback"
    assert body["advice"] == "FALLBACK SAFETY NOTICE"
    assert body["missing_configuration"] == ["LLM_API_KEY"]


def test_advise_rejects_more_than_ten_medications(client):
    response = client.post(
        "/advise",
        json={
            "meds": [f"drug {i}" for i in range(11)],
            "schedule": ["1+0+1"] * 11,
            "age": 45,
            "gender": "F",
        },
    )
    assert response.status_code == 422


def test_drug_interactions_requires_two_medications(client):
    response = client.post("/drug_interactions", json={"medications": ["aspirin"]})
    assert response.status_code == 422


def test_drug_interactions_returns_enhanced_shape(client, monkeypatch):
    monkeypatch.setattr(main, "services", _FakeContainer())

    class _GraphWithInteraction(_FakeKnowledgeGraph):
        def analyze_drug_interactions(self, medications):
            return [
                {
                    "drug1": "warfarin",
                    "drug2": "aspirin",
                    "severity": "major",
                    "risk": "bleeding",
                    "category": "pharmacodynamic",
                    "description": "Additive bleeding risk.",
                    "mechanism": "Anticoagulant + antiplatelet.",
                    "clinical_significance": "Haemorrhage risk.",
                    "management_strategy": "Avoid.",
                }
            ]

    container = _FakeContainer()
    container.knowledge_graph = lambda: _GraphWithInteraction()
    monkeypatch.setattr(main, "services", container)

    response = client.post(
        "/drug_interactions",
        json={"medications": ["warfarin", "aspirin"], "patient_info": {"age": 70}},
    )

    assert response.status_code == 200
    interaction = response.json()["data"][0]
    assert interaction["description"] == "Additive bleeding risk."
    assert interaction["category"] == "pharmacodynamic"
    assert interaction["mechanism"]
    assert interaction["risk_factors"]


def test_exported_html_escapes_model_output():
    rendered = _convert_markdown_to_html_content("<script>alert('x')</script>\n\n## Safe heading")

    assert "<script" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "<h2>Safe heading</h2>" in rendered


def test_api_key_is_enforced_when_configured(monkeypatch):
    _reset_rate_limit()
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: SimpleNamespace(api_key=SecretStr("secret"), rate_limit_per_minute=10),
    )
    request = SimpleNamespace(
        headers={"x-api-key": "wrong"}, client=SimpleNamespace(host="10.0.0.1")
    )

    with pytest.raises(HTTPException) as excinfo:
        _enforce_access(request)

    assert excinfo.value.status_code == 401


def test_rate_limit_returns_429(monkeypatch):
    _reset_rate_limit()
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: SimpleNamespace(api_key=None, rate_limit_per_minute=2),
    )
    request = SimpleNamespace(headers={}, client=SimpleNamespace(host="10.0.0.2"))

    _enforce_access(request)
    _enforce_access(request)
    with pytest.raises(HTTPException) as excinfo:
        _enforce_access(request)

    assert excinfo.value.status_code == 429
