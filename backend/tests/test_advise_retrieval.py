from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

import app.main as main
from src.models.schemas import MedicationInfo
from src.services.jina_scraper import MedexPage
from src.services.medical_knowledge_graph import MedicalKnowledgeGraph

PUBMED_URL = "https://pubmed.ncbi.nlm.nih.gov/38205598/"
DEMO_REQUEST = {
    "meds": ["Comet 500", "Amdocal 5"],
    "schedule": ["1+0+1", "1+0+0"],
    "age": 58,
    "gender": "M",
    "conditions": ["type 2 diabetes", "hypertension"],
}
GENERICS = {
    "Comet 500": "Metformin Hydrochloride",
    "Amdocal 5": "Amlodipine Besilate",
    "Atova 10": "Atorvastatin Calcium",
}


@pytest.fixture(autouse=True)
def empty_advice_cache() -> None:
    main.advice_cache.clear()


def _scrape_by_brand(url: str) -> MedexPage | None:
    brand = url.removeprefix("https://medex.com.bd/")
    return (
        MedexPage(text=f"{brand} monograph", generic_name=GENERICS[brand])
        if brand in GENERICS
        else None
    )


def _demo_services(generate: AsyncMock) -> SimpleNamespace:
    return SimpleNamespace(
        all_available=lambda: True,
        drug_lookup=lambda: SimpleNamespace(
            find_drug_url=lambda name: f"https://medex.com.bd/{name}"
        ),
        jina_scraper=lambda: SimpleNamespace(scrape_medex_page=_scrape_by_brand),
        knowledge_graph=MedicalKnowledgeGraph,
        vector_search=lambda: SimpleNamespace(
            enhanced_medical_search=Mock(return_value=[{"title": "Evidence", "source": PUBMED_URL}])
        ),
        llm_client=lambda: SimpleNamespace(
            is_available=True, generate_medication_advice=generate, missing_configuration=lambda: []
        ),
    )


@pytest.mark.parametrize(("from_llm", "model_calls"), [(True, 1), (False, 2)])
def test_repeat_consultation_reuses_only_model_written_advice(
    monkeypatch: pytest.MonkeyPatch, from_llm: bool, model_calls: int
) -> None:
    generate = AsyncMock(return_value=SimpleNamespace(text="Advice.", from_llm=from_llm))
    monkeypatch.setattr(main, "services", _demo_services(generate))
    client = TestClient(main.app)

    first = client.post("/advise", json=DEMO_REQUEST)
    second = client.post("/advise", json=DEMO_REQUEST)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert generate.await_count == model_calls


def test_interaction_check_resolves_brands_to_active_ingredients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "services", _demo_services(AsyncMock()))

    response = TestClient(main.app).post(
        "/drug_interactions", json={"medications": ["Amdocal 5", "Atova 10", "Unlisted 20"]}
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert [interaction["medications"] for interaction in body["data"]] == [
        ["Amdocal 5 (amlodipine)", "Simvastatin 20 (simvastatin)"]
    ]
    assert body["data"][0]["severity"] == "moderate"
    assert body["data"][0]["risk_factors"] == []
    assert body["checked"] == [
        {
            "name": "Amdocal 5",
            "generic_name": "Amlodipine Besilate",
            "found_in_database": True,
            "ingredients": ["amlodipine"],
        },
        {
            "name": "Atova 10",
            "generic_name": "Atorvastatin Calcium",
            "found_in_database": True,
            "ingredients": ["atorvastatin"],
        },
        {
            "name": "Simvastatin 20",
            "generic_name": None,
            "found_in_database": True,
            "ingredients": ["simvastatin"],
        },
    ]
    assert body["known_interactions"] == 5


@pytest.mark.parametrize(
    ("generic_name", "expected"),
    [
        ("Metformin Hydrochloride", ["metformin"]),
        ("Amlodipine Besilate", ["amlodipine"]),
        (" Amlodipine Besilate + Metformin Hydrochloride ", ["amlodipine", "metformin"]),
        (None, ["comet"]),
    ],
)
def test_medication_active_ingredients(generic_name: str | None, expected: list[str]) -> None:
    medication = MedicationInfo(name="Comet 500", generic_name=generic_name, schedule="1+0+1")

    assert medication.active_ingredients == expected


@pytest.mark.parametrize(
    ("brand", "generic", "ingredient", "interactions_found"),
    [
        ("Amdocal 5", "Amlodipine Besilate", "amlodipine", 0),
        ("Amdocal 5", None, "amdocal", 0),
        ("Actrapid 100", "Insulin Human", "insulin", 1),
    ],
)
def test_advise_uses_medex_generics_and_conditions_and_returns_article_links(
    monkeypatch: pytest.MonkeyPatch,
    brand: str,
    generic: str | None,
    ingredient: str,
    interactions_found: int,
) -> None:
    comet_text = "Comet monograph"
    second_monograph = f"{brand} monograph"
    scrape = Mock(
        side_effect=[
            MedexPage(text=comet_text, generic_name="Metformin Hydrochloride"),
            MedexPage(text=second_monograph, generic_name=generic),
        ]
    )
    search = Mock(
        return_value=[
            {"title": "Metformin evidence", "source": PUBMED_URL},
            {"title": "Other evidence", "url": PUBMED_URL, "source": "PubMed"},
            {"title": "Without link", "source": "PubMed"},
            {"title": "Placeholder", "url": "#"},
        ]
    )
    generate = AsyncMock(return_value=SimpleNamespace(text="Evidence summary.", from_llm=True))
    services = SimpleNamespace(
        all_available=lambda: True,
        drug_lookup=lambda: SimpleNamespace(
            find_drug_url=lambda name: f"https://medex.com.bd/{name}"
        ),
        jina_scraper=lambda: SimpleNamespace(scrape_medex_page=scrape),
        knowledge_graph=MedicalKnowledgeGraph,
        vector_search=lambda: SimpleNamespace(enhanced_medical_search=search),
        llm_client=lambda: SimpleNamespace(
            is_available=True, generate_medication_advice=generate, missing_configuration=lambda: []
        ),
    )
    monkeypatch.setattr(main, "services", services)

    response = TestClient(main.app).post(
        "/advise",
        json={
            "meds": ["Comet 500", brand],
            "schedule": ["1+0+1", "1+0+0"],
            "age": 58,
            "gender": "M",
            "conditions": ["type 2 diabetes", "hypertension"],
        },
    )

    assert response.status_code == 200, response.text
    query = search.call_args.kwargs["query"].lower()
    assert "metformin hydrochloride" in query
    assert "type 2 diabetes" in query
    assert "hypertension" in query
    assert "comet" not in query
    assert (generic or brand).lower() in query
    assert search.call_args.kwargs["medications"] == ["metformin", ingredient]
    body = response.json()
    assert body["drug_interactions_found"] == interactions_found
    assert [article["url"] for article in body["context_sources"]] == [
        PUBMED_URL,
        PUBMED_URL,
        None,
        None,
    ]
    assert body["advice"] == "Evidence summary."
    assert generate.call_args.kwargs["medex_context"] == [comet_text, second_monograph]
