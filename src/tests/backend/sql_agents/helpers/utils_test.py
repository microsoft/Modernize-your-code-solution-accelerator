"""Tests for sql_agents/helpers/utils.py module."""

from unittest.mock import mock_open, patch

from backend.sql_agents.helpers.utils import get_prompt, is_text

import pytest


class TestGetPrompt:
    """Tests for get_prompt function."""

    def test_get_prompt_success(self):
        """Test successful prompt retrieval."""
        expected_content = "This is a test prompt for the agent."

        with patch("builtins.open", mock_open(read_data=expected_content)):
            result = get_prompt("migrator")
            assert result == expected_content

    def test_get_prompt_invalid_agent_type(self):
        """Test with invalid agent type containing special characters."""
        with pytest.raises(ValueError, match="Invalid agent type"):
            get_prompt("../malicious/path")

    def test_get_prompt_invalid_agent_type_special_chars(self):
        """Test with agent type containing special characters."""
        with pytest.raises(ValueError, match="Invalid agent type"):
            get_prompt("agent;drop table")

    def test_get_prompt_invalid_agent_type_spaces(self):
        """Test with agent type containing spaces."""
        with pytest.raises(ValueError, match="Invalid agent type"):
            get_prompt("agent name")

    def test_get_prompt_valid_agent_types(self):
        """Test with various valid agent type formats."""
        with patch("builtins.open", mock_open(read_data="content")):
            # Should not raise for valid patterns
            result = get_prompt("migrator")
            assert result == "content"

            result = get_prompt("syntax_checker")
            assert result == "content"

            result = get_prompt("Agent123")
            assert result == "content"

    def test_get_prompt_file_not_found(self):
        """Test when prompt file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                get_prompt("nonexistent")


class TestIsText:
    """Tests for is_text function."""

    def test_is_text_with_sql(self):
        """Test is_text with valid SQL content."""
        sql_content = "SELECT * FROM users WHERE id = 1"
        assert is_text(sql_content) is True

    def test_is_text_with_non_empty_string(self):
        """Test is_text with any non-empty string returns True."""
        content = "\x00\x01\x02\x03\x04"
        # is_text returns True for any non-empty string
        assert is_text(content) is True

    def test_is_text_with_empty_string(self):
        """Test is_text with empty string returns False."""
        # Empty strings return False per the implementation
        assert is_text("") is False

    def test_is_text_with_multiline_sql(self):
        """Test is_text with multiline SQL."""
        sql_content = """
        SELECT u.id, u.name
        FROM users u
        WHERE u.active = 1
        ORDER BY u.name
        """
        assert is_text(sql_content) is True
