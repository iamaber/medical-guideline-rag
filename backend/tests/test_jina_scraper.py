from unittest.mock import Mock

import pytest
from requests import Response

from src.services.jina_scraper import JinaScraper

COMET_URL = "https://medex.com.bd/brands/5359/comet-500-mg-tablet"


@pytest.fixture
def comet_jina_response() -> tuple[str, str]:
    monograph = (
        "Title: Comet Tablet 500 mg (কমেট ৫০০ মি.গ্রা.)\n\n"
        f"URL Source: {COMET_URL}\n\n"
        "Markdown Content:\n"
        "500 mg\n"
    )
    links = (
        "\nLinks/Buttons:\n"
        "- [Brand Names (Allopathic)](https://medex.com.bd/brands)\n"
        "- [Generics (Allopathic)](https://medex.com.bd/generics)\n"
        "- [Metformin Hydrochloride](https://medex.com.bd/generics/734/metformin-hydrochloride)\n"
        "- [Alternate Brands]"
        "(https://medex.com.bd/generics/734/metformin-hydrochloride/brand-names)\n"
    )
    return monograph, links


@pytest.mark.parametrize("with_links", [True, False])
def test_scraped_page_returns_monograph_and_generic(
    monkeypatch: pytest.MonkeyPatch, comet_jina_response: tuple[str, str], with_links: bool
) -> None:
    monograph, links = comet_jina_response
    body = monograph + links if with_links else monograph
    scraper = JinaScraper()
    response = Mock(spec=Response, status_code=200, text=body)
    get = Mock(return_value=response)
    monkeypatch.setattr(scraper.session, "get", get)

    page = scraper.scrape_medex_page(COMET_URL)

    assert page is not None
    assert page.text == monograph
    assert page.generic_name == ("Metformin Hydrochloride" if with_links else None)
    assert get.call_args.kwargs["headers"]["X-With-Links-Summary"] == "true"
