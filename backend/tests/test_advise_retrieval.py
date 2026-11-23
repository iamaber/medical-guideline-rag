from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

import app.main as main
from src.services.jina_scraper import MedexPage

PUBMED_URL = "https://pubmed.ncbi.nlm.nih.gov/38205598/"


@pytest.mark.parametrize("amdocal_generic", ["Amlodipine Besilate", None])
def test_advise_uses_medex_generics_and_conditions_and_returns_article_links(
    monkeypatch: pytest.MonkeyPatch, amdocal_generic: str | None
) -> None:
    comet_text = "Comet monograph"
    amdocal_text = "Amdocal monograph"
    scrape = Mock(
        side_effect=[
            MedexPage(text=comet_text, generic_name="Metformin Hydrochloride"),
            MedexPage(text=amdocal_text, generic_name=amdocal_generic),
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
        knowledge_graph=lambda: SimpleNamespace(analyze_drug_interactions=lambda meds: []),
        vector_search=lambda: SimpleNamespace(enhanced_medical_search=search),
        llm_client=lambda: SimpleNamespace(
            is_available=True, generate_medication_advice=generate, missing_configuration=lambda: []
        ),
    )
    monkeypatch.setattr(main, "services", services)

    response = TestClient(main.app).post(
        "/advise",
        json={
            "meds": ["Comet 500", "Amdocal 5"],
            "schedule": ["1+0+1", "1+0+0"],
            "age": 58,
            "gender": "M",
            "conditions": ["type 2 diabetes", "hypertension"],
        },
    )

    assert response.status_code == 200, response.text
    query = search.call_args.kwargs["query"].lower()
    assert "metformin" in query
    assert "type 2 diabetes" in query
    assert "hypertension" in query
    assert "comet" not in query
    assert (amdocal_generic or "Amdocal 5").lower() in query
    assert search.call_args.kwargs["medications"] == [
        "Metformin Hydrochloride",
        amdocal_generic or "Amdocal 5",
    ]
    body = response.json()
    assert [article["url"] for article in body["context_sources"]] == [
        PUBMED_URL,
        PUBMED_URL,
        None,
        None,
    ]
    assert body["advice"] == "Evidence summary."
    assert generate.call_args.kwargs["medex_context"] == [comet_text, amdocal_text]
