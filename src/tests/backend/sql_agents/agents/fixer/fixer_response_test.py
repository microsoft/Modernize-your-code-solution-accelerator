from pydantic_core import ValidationError

import pytest

from sql_agents.agents.fixer.response import FixerResponse


def test_fixer_response_creation_all_fields():
    """Test creating FixerResponse with all fields."""
    response = FixerResponse(
        thought="Analyzing query structure",
        fixed_query="SELECT * FROM users",
        summary="Corrected syntax error"
    )

    assert response.thought == "Analyzing query structure"
    assert response.fixed_query == "SELECT * FROM users"
    assert response.summary == "Corrected syntax error"


def test_fixer_response_creation_optional_summary():
    """Test creating FixerResponse without optional summary."""
    response = FixerResponse(
        thought="Fix completed",
        fixed_query="SELECT name FROM customers",
        summary=None
    )

    assert response.thought == "Fix completed"
    assert response.fixed_query == "SELECT name FROM customers"
    assert response.summary is None


def test_fixer_response_invalid_field_types():
    """Test FixerResponse raises error for invalid field types."""
    with pytest.raises(ValidationError, match="Input should be a valid string"):
        FixerResponse(
            thought=123,  # Invalid type
            fixed_query=["SELECT * FROM orders"],  # Invalid type
            summary=456  # Should be str or None
        )
