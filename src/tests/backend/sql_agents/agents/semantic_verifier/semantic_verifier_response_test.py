import pytest

from sql_agents.agents.semantic_verifier.response import SemanticVerifierResponse


def test_semantic_verifier_response_initialization():
    """Test initializing SemanticVerifierResponse with valid data."""
    response = SemanticVerifierResponse(
        judgement="valid",
        differences=["difference1", "difference2"],
        summary="This is a summary."
    )
    assert response.judgement == "valid"
    assert response.differences == ["difference1", "difference2"]
    assert response.summary == "This is a summary."


def test_semantic_verifier_response_empty_fields():
    """Test initializing SemanticVerifierResponse with empty fields."""
    response = SemanticVerifierResponse(
        judgement="",
        differences=[],
        summary=""
    )
    assert response.judgement == ""
    assert response.differences == []
    assert response.summary == ""


def test_semantic_verifier_response_invalid_data():
    """Test initializing SemanticVerifierResponse with invalid data."""
    with pytest.raises(ValueError):
        SemanticVerifierResponse(
            judgement=123,  # Invalid type
            differences="not a list",  # Invalid type
            summary=None  # Invalid type
        )


def test_semantic_verifier_response_large_differences():
    """Test initializing SemanticVerifierResponse with a large number of differences."""
    differences = [f"difference{i}" for i in range(1000)]  # Large list of differences
    response = SemanticVerifierResponse(
        judgement="valid",
        differences=differences,
        summary="This is a summary."
    )
    assert len(response.differences) == 1000
    assert response.judgement == "valid"
    assert response.summary == "This is a summary."


def test_semantic_verifier_response_special_characters():
    """Test initializing SemanticVerifierResponse with special characters."""
    response = SemanticVerifierResponse(
        judgement="valid!@#$%^&*()",
        differences=["difference1", "difference2"],
        summary="This is a summary with special characters!@#$%^&*()"
    )
    assert response.judgement == "valid!@#$%^&*()"
    assert response.differences == ["difference1", "difference2"]
    assert response.summary == "This is a summary with special characters!@#$%^&*()"
