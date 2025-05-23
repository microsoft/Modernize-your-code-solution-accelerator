from sql_agents.agents.picker.response import PickerResponse


def test_picker_response_all_fields():
    """Test PickerResponse with all fields provided."""
    response = PickerResponse(
        conclusion="Chosen candidate is accurate.",
        picked_query="SELECT * FROM users",
        summary="Summary of the selection process."
    )

    assert response.conclusion == "Chosen candidate is accurate."
    assert response.picked_query == "SELECT * FROM users"
    assert response.summary == "Summary of the selection process."


def test_picker_response_optional_summary_none():
    """Test PickerResponse when optional summary is None."""
    response = PickerResponse(
        conclusion="No valid candidates.",
        picked_query="SELECT * FROM fallback",
        summary=None
    )

    assert response.summary is None
    assert response.picked_query == "SELECT * FROM fallback"
