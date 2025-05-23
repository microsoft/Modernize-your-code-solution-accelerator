from sql_agents.agents.migrator.response import MigratorCandidate, MigratorResponse


def test_migrator_candidate_creation():
    """Test that MigratorCandidate can be created successfully."""
    candidate = MigratorCandidate(plan="Use LEFT JOIN", candidate_query="SELECT * FROM table1 LEFT JOIN table2")
    assert candidate.plan == "Use LEFT JOIN"
    assert candidate.candidate_query == "SELECT * FROM table1 LEFT JOIN table2"


def test_migrator_response_full():
    """Test full MigratorResponse with all fields populated."""
    candidate = MigratorCandidate(plan="Use JOIN", candidate_query="SELECT * FROM A JOIN B")
    response = MigratorResponse(
        input_summary="Translates query logic",
        candidates=[candidate],
        input_error="Syntax error in original query",
        summary="Final version corrected",
        rai_error="RAI flag triggered"
    )
    assert response.input_summary == "Translates query logic"
    assert len(response.candidates) == 1
    assert response.input_error == "Syntax error in original query"
    assert response.summary == "Final version corrected"
    assert response.rai_error == "RAI flag triggered"


def test_migrator_response_defaults():
    """Test MigratorResponse with only required fields."""
    candidate = MigratorCandidate(plan="Use EXISTS", candidate_query="SELECT ...")
    response = MigratorResponse(input_summary="Check optimization", candidates=[candidate])
    assert response.input_error is None
    assert response.summary is None
    assert response.rai_error is None
