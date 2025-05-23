from unittest import mock

import pytest

from sql_agents.helpers.utils import get_prompt, is_text


def test_get_prompt_valid_agent_type():
    agent_type = "agent1"

    # Mock the file reading
    with mock.patch("builtins.open", mock.mock_open(read_data="This is the prompt")):
        prompt = get_prompt(agent_type)

    # Assert the prompt returned is correct
    assert prompt == "This is the prompt"


def test_get_prompt_invalid_agent_type():
    agent_type = "invalid-agent!"  # Invalid agent type with a non-alphanumeric character

    # Expect a ValueError to be raised for an invalid agent type
    with pytest.raises(ValueError):
        get_prompt(agent_type)


def test_get_prompt_file_not_found():
    agent_type = "agent1"

    # Mock os.path.join and the file not being found
    with mock.patch("builtins.open", mock.mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError
        with pytest.raises(FileNotFoundError):
            get_prompt(agent_type)


# Test for the is_text function
def test_is_text_empty_string():
    """Test when the content is an empty string."""
    assert not is_text("")


def test_is_text_non_empty_string():
    """Test when the content is a non-empty string."""
    assert is_text("Hello, world!")
