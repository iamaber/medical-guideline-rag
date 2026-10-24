"""Drug lookup resolution tests."""

import json

import pytest

from src.services.drug_lookup import DrugLookup


@pytest.fixture()
def drug_lookup(tmp_path):
    brands = [
        {"brand_name": "Adol 500", "brand_url": "https://example.test/adol-500"},
        {"brand_name": "Adol 650", "brand_url": "https://example.test/adol-650"},
        {"brand_name": "Napa Extra", "brand_url": "https://example.test/napa-extra"},
        {"brand_name": "Seclo 20", "brand_url": "https://example.test/seclo-20"},
    ]
    db_path = tmp_path / "medex_URL.json"
    db_path.write_text(json.dumps({"brands": brands}), encoding="utf-8")
    return DrugLookup(db_path=str(db_path))


def test_exact_match_is_case_and_separator_insensitive(drug_lookup):
    assert drug_lookup.find_drug_url("adol 500") == "https://example.test/adol-500"
    assert drug_lookup.find_drug_url("NAPA-EXTRA") == "https://example.test/napa-extra"
    assert drug_lookup.find_drug_url("  Seclo 20 ") == "https://example.test/seclo-20"


def test_ambiguous_prefix_returns_none_instead_of_arbitrary_brand(drug_lookup):
    assert drug_lookup.find_drug_url("Adol") is None


def test_unambiguous_partial_match_is_resolved(drug_lookup):
    assert drug_lookup.find_drug_url("napa") == "https://example.test/napa-extra"


def test_unknown_drug_returns_none(drug_lookup):
    assert drug_lookup.find_drug_url("not-a-real-drug") is None
    assert drug_lookup.find_drug_url("") is None


def test_search_sorts_before_applying_limit(drug_lookup):
    results = drug_lookup.search_drugs("adol", limit=1)
    assert results == ["Adol 500"]

    all_results = drug_lookup.search_drugs("adol", limit=10)
    assert all_results == ["Adol 500", "Adol 650"]
