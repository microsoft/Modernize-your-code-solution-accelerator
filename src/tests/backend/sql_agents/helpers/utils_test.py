"""Tests for sql_agents/helpers/utils.py module."""

import os
import tempfile
from unittest.mock import patch, mock_open

import pytest

from backend.sql_agents.helpers.utils import get_prompt, is_text


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

    def test_is_text_with_valid_string(self):
        """Test with valid non-empty string."""
        assert is_text("SELECT * FROM table") is True

    def test_is_text_with_empty_string(self):
        """Test with empty string."""
        assert is_text("") is False

    def test_is_text_with_whitespace_string(self):
        """Test with whitespace-only string."""
        assert is_text("   ") is True

    def test_is_text_with_none(self):
        """Test with None value."""
        # is_text checks isinstance(content, str), so None should return True
        # as it doesn't match the str check with len == 0
        assert is_text(None) is True

    def test_is_text_with_bytes(self):
        """Test with bytes."""
        assert is_text(b"binary content") is True

    def test_is_text_with_list(self):
        """Test with list."""
        assert is_text(["item1", "item2"]) is True

    def test_is_text_with_number(self):
        """Test with number."""
        assert is_text(123) is True

    def test_is_text_with_multiline_string(self):
        """Test with multiline string."""
        content = """
        SELECT *
        FROM table
        WHERE id = 1
        """
        assert is_text(content) is True

    def test_is_text_with_unicode(self):
        """Test with unicode characters."""
        assert is_text("SELECT * FROM таблица") is True
