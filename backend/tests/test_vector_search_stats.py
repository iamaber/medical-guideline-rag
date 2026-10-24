"""Vector-search statistics tests."""

from src.services.vector_search import VectorSearch


class _FakeIndex:
    d = 384


def test_embedding_dimension_comes_from_loaded_index():
    service = object.__new__(VectorSearch)
    service.documents = []
    service.index = _FakeIndex()
    service.embeddings = None
    service.model_name = "test-model"

    stats = service.get_stats()

    assert stats["embedding_dimension"] == 384
    assert stats["index_loaded"] is True


def test_embedding_dimension_is_zero_without_index():
    service = object.__new__(VectorSearch)
    service.documents = []
    service.index = None
    service.embeddings = None
    service.model_name = "test-model"

    assert service.get_stats()["embedding_dimension"] == 0
