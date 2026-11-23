from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

import app.main as main
from src.models.schemas import MedicationInfo
from src.services.jina_scraper import MedexPage
from src.services.medical_knowledge_graph import MedicalKnowledgeGraph

PUBMED_URL = "https://pubmed.ncbi.nlm.nih.gov/38205598/"


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
