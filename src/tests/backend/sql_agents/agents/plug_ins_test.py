"""Tests for sql_agents/agents/syntax_checker/plug_ins.py module."""
# pylint: disable=protected-access

import subprocess
from unittest.mock import MagicMock, patch

from backend.sql_agents.agents.syntax_checker.plug_ins import SyntaxCheckerPlugin


class TestSyntaxCheckerPlugin:
    """Tests for SyntaxCheckerPlugin class."""

    def test_check_syntax_calls_parser(self):
        """Test check_syntax calls the parser."""
        plugin = SyntaxCheckerPlugin()

        with patch.object(plugin, '_call_tsqlparser', return_value='[]') as mock_parser:
            result = plugin.check_syntax("SELECT * FROM table")

            mock_parser.assert_called_once_with("SELECT * FROM table")
            assert result == '[]'

    def test_call_tsqlparser_windows(self):
        """Test _call_tsqlparser on Windows."""
        plugin = SyntaxCheckerPlugin()

        with patch('platform.system', return_value='Windows'):
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.stdout = '[]'
                mock_run.return_value = mock_result

                plugin._call_tsqlparser("SELECT * FROM table")

                mock_run.assert_called_once()
                # Check that the Windows executable path is used
                call_args = mock_run.call_args[0][0]
                assert 'win-x64' in call_args[0]

    def test_call_tsqlparser_linux(self):
        """Test _call_tsqlparser on Linux."""
        plugin = SyntaxCheckerPlugin()

        with patch('platform.system', return_value='Linux'):
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.stdout = '[]'
                mock_run.return_value = mock_result

                plugin._call_tsqlparser("SELECT * FROM table")

                mock_run.assert_called_once()
                # Check that the Linux executable path is used
                call_args = mock_run.call_args[0][0]
                assert 'linux-x64' in call_args[0]

    def test_call_tsqlparser_success(self):
        """Test successful parser execution."""
        plugin = SyntaxCheckerPlugin()
        expected_output = '[{"Line": 1, "Column": 5, "Error": "Syntax error"}]'

        with patch('platform.system', return_value='Windows'):
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.stdout = expected_output
                mock_run.return_value = mock_result

                result = plugin._call_tsqlparser("SELECT * FROM")

                assert result == expected_output

    def test_call_tsqlparser_called_process_error(self):
        """Test parser execution with CalledProcessError."""
        plugin = SyntaxCheckerPlugin()

        with patch('platform.system', return_value='Windows'):
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    returncode=1,
                    cmd=['parser'],
                    output="Error output"
                )

                result = plugin._call_tsqlparser("INVALID SQL")

                assert result == ""

    def test_call_tsqlparser_generic_exception(self):
        """Test parser execution with generic exception."""
        plugin = SyntaxCheckerPlugin()

        with patch('platform.system', return_value='Windows'):
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = Exception("Unexpected error")

                result = plugin._call_tsqlparser("SELECT * FROM table")

                assert result is None
