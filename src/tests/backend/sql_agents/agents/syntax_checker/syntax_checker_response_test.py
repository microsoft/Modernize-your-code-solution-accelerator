from sql_agents.agents.syntax_checker.response import SyntaxCheckerResponse, SyntaxErrorInt


def test_syntax_error_int_initialization():
    """Test initializing SyntaxErrorInt with valid data."""
    syntax_error = SyntaxErrorInt(line=1, column=5, error="Syntax error")
    assert syntax_error.line == 1
    assert syntax_error.column == 5
    assert syntax_error.error == "Syntax error"


def test_syntax_checker_response_initialization():
    """Test initializing SyntaxCheckerResponse with valid data."""
    syntax_error = SyntaxErrorInt(line=1, column=5, error="Syntax error")
    response = SyntaxCheckerResponse(
        thought="Analyzing SQL query",
        syntax_errors=[syntax_error],
        summary="1 syntax error found"
    )
    assert response.thought == "Analyzing SQL query"
    assert len(response.syntax_errors) == 1
    assert response.syntax_errors[0].line == 1
    assert response.syntax_errors[0].column == 5
    assert response.syntax_errors[0].error == "Syntax error"
    assert response.summary == "1 syntax error found"


def test_syntax_checker_response_empty_fields():
    """Test initializing SyntaxCheckerResponse with empty fields."""
    response = SyntaxCheckerResponse(
        thought="",
        syntax_errors=[],
        summary=""
    )
    assert response.thought == ""
    assert response.syntax_errors == []
    assert response.summary == ""
