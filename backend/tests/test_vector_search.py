from typing import Any

import pytest

from src.services.vector_search import VectorSearch


def _record(
    pmid: int, section: str, score: float, content: str, mesh_terms: tuple[str, ...] = ()
) -> dict[str, Any]:
    return {
        "id": f"{pmid}_{section}",
        "source": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "relevance_score": score,
        "content": content,
        "mesh_terms": list(mesh_terms),
    }


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> VectorSearch:
    monkeypatch.setattr(VectorSearch, "_load_model", lambda self: None)
    return VectorSearch()


def test_keeps_highest_ranked_record_per_article(
    service: VectorSearch, monkeypatch: pytest.MonkeyPatch
) -> None:
    top = _record(100, "abstract", 0.95, "Amlodipine abstract")
    duplicate = _record(100, "title", 0.85, "Amlodipine title")
    other = _record(200, "abstract", 0.75, "Another amlodipine article")
    records = [top, duplicate, other]
    monkeypatch.setattr(service, "search", lambda query, k: records[:k])

    assert service.enhanced_medical_search("amlodipine", k=3) == [top, other]


def test_refills_with_distinct_articles_from_expansion_and_original_search(
    service: VectorSearch, monkeypatch: pytest.MonkeyPatch
) -> None:
    top = _record(100, "abstract", 0.95, "Amlodipine abstract", ("Hypertension",))
    duplicate = _record(100, "title", 0.90, "Amlodipine title")
    third_section = _record(100, "methods", 0.85, "Amlodipine study methods")
    expanded = _record(200, "abstract", 0.80, "Amlodipine for hypertension")
    original = _record(300, "abstract", 0.75, "Managing high blood pressure")
    records_by_query = {
        "amlodipine": [top, duplicate, third_section, original],
        "amlodipine hypertension": [duplicate, expanded],
    }
    monkeypatch.setattr(service, "search", lambda query, k: records_by_query[query][:k])

    assert service.enhanced_medical_search("amlodipine", medications=["amlodipine"], k=3) == [
        top,
        expanded,
        original,
    ]


def test_empty_medication_filter_falls_back_to_distinct_articles(
    service: VectorSearch, monkeypatch: pytest.MonkeyPatch
) -> None:
    top = _record(100, "abstract", 0.95, "Blood pressure in type 2 diabetes")
    duplicate = _record(100, "title", 0.85, "Blood pressure and diabetes")
    second = _record(200, "abstract", 0.80, "Managing high blood pressure")
    third = _record(300, "abstract", 0.75, "Hypertension guidelines")
    records = [top, duplicate, second, third]
    monkeypatch.setattr(service, "search", lambda query, k: records[:k])

    assert service.enhanced_medical_search("hypertension", medications=["amlodipine"], k=3) == [
        top,
        second,
        third,
    ]


@pytest.mark.parametrize(
    "generic", ["Metformin Hydrochloride", "Amlodipine Besilate + Metformin Hydrochloride"]
)
def test_medication_salt_matches_base_name_in_abstract(
    service: VectorSearch, monkeypatch: pytest.MonkeyPatch, generic: str
) -> None:
    unrelated = _record(100, "abstract", 0.95, "Insulin for type 2 diabetes")
    match = _record(200, "abstract", 0.85, "Metformin for type 2 diabetes")
    records = [unrelated, match]
    monkeypatch.setattr(service, "search", lambda query, k: records[:k])

    assert service.enhanced_medical_search(
        f"{generic} type 2 diabetes", medications=[generic], k=1
    ) == [match]


def test_besilate_salt_matches_amlodipine_abstract(
    service: VectorSearch, monkeypatch: pytest.MonkeyPatch
) -> None:
    unrelated = _record(100, "abstract", 0.95, "Telmisartan for hypertension")
    match = _record(200, "abstract", 0.85, "Amlodipine for hypertension")
    records = [unrelated, match]
    monkeypatch.setattr(service, "search", lambda query, k: records[:k])

    assert service.enhanced_medical_search(
        "amlodipine besilate hypertension", medications=["Amlodipine Besilate"], k=1
    ) == [match]
