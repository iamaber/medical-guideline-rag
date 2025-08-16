"""Basic tests for the medical guideline RAG system."""

import sys
from pathlib import Path

# Add src to Python path for testing
sys.path.append(str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all modules can be imported."""
    try:
        from src.models.schemas import UserInput, GenderEnum
        from src.services.drug_lookup import DrugLookup
        from src.utils.text_processor import TextProcessor

        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"


def test_user_input_schema():
    """Test UserInput schema validation."""
    from src.models.schemas import UserInput, GenderEnum

    # Test valid input
    valid_input = {
        "meds": ["Test Medicine"],
        "schedule": ["1+0+1"],
        "age": 25,
        "gender": GenderEnum.MALE,
    }

    user_input = UserInput(**valid_input)
    assert user_input.meds == ["Test Medicine"]
    assert user_input.age == 25
    assert user_input.gender == GenderEnum.MALE


def test_text_processor():
    """Test text processing functionality."""
    from src.utils.text_processor import TextProcessor

    processor = TextProcessor()

    # Test text cleaning
    dirty_text = "<p>This is a test with <b>HTML</b> tags and [1] citations.</p>"
    clean_text = processor.clean_text(dirty_text)

    assert "<p>" not in clean_text
    assert "<b>" not in clean_text
    assert "[1]" not in clean_text
    assert "test" in clean_text


def test_drug_lookup_init():
    """Test drug lookup service initialization."""
    from src.services.drug_lookup import DrugLookup

    # Test initialization (should handle missing file gracefully)
    lookup = DrugLookup(db_path="nonexistent_file.json")
    assert isinstance(lookup.drug_db, dict)
    assert len(lookup.drug_db) == 0  # Should be empty if file doesn't exist


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
