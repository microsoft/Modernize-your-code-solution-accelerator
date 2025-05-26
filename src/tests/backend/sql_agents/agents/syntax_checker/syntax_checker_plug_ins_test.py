from unittest.mock import MagicMock, patch

import pytest

from sql_agents.agents.syntax_checker.plug_ins import SyntaxCheckerPlugin


@pytest.fixture
def syntax_checker_plugin():
    """Fixture to create a SyntaxCheckerPlugin instance."""
    return SyntaxCheckerPlugin()


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_windows_path(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method on Windows."""
    with patch("platform.system", return_value="Windows"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = "SELECT * FROM table"
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            [r".\sql_agents\tools\win-x64\tsqlParser.exe", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_linux_path(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method on Linux."""
    with patch("platform.system", return_value="Linux"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = "SELECT * FROM table"
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            ["./sql_agents/tools/linux-x64/tsqlParser", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_other_os(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method on other OS."""
    with patch("platform.system", return_value="Other"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = "SELECT * FROM table"
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            ["./sql_agents/tools/linux-x64/tsqlParser", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_empty_string(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method with an empty string."""
    with patch("platform.system", return_value="Windows"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = ""
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            [r".\sql_agents\tools\win-x64\tsqlParser.exe", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_empty_string_linux(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method with an empty string."""
    with patch("platform.system", return_value="Linux"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = ""
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            ["./sql_agents/tools/linux-x64/tsqlParser", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_empty_string_other_os(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method with an empty string."""
    with patch("platform.system", return_value="Other"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = ""
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            ["./sql_agents/tools/linux-x64/tsqlParser", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_invalid_sql(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method with invalid SQL."""
    with patch("platform.system", return_value="Windows"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = "INVALID SQL"
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            [r".\sql_agents\tools\win-x64\tsqlParser.exe", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_invalid_sql_linux(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method with invalid SQL."""
    with patch("platform.system", return_value="Linux"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = "INVALID SQL"
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            ["./sql_agents/tools/linux-x64/tsqlParser", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_invalid_sql_other_os(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method with invalid SQL."""
    with patch("platform.system", return_value="Other"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = "INVALID SQL"
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            ["./sql_agents/tools/linux-x64/tsqlParser", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )


@patch("sql_agents.agents.syntax_checker.plug_ins.subprocess.run")
def test_check_syntax_valid_sql(mock_subprocess_run, syntax_checker_plugin):
    """Test the _call_tsqlparser method with valid SQL."""
    with patch("platform.system", return_value="Windows"):
        mock_subprocess_run.return_value = MagicMock(stdout="[]")
        candidate_sql = "SELECT * FROM table"
        result = syntax_checker_plugin.check_syntax(candidate_sql)
        assert result == "[]"
        mock_subprocess_run.assert_called_once_with(
            [r".\sql_agents\tools\win-x64\tsqlParser.exe", "--string", candidate_sql],
            capture_output=True,
            text=True,
            check=True,
        )
