"""Utility functions for the backend package."""

import os
import re


def get_prompt(agent_type: str) -> str:
    """Get the prompt for the given agent type."""
    if not re.match(r"^[a-zA-Z0-9_]+$", agent_type):
        raise ValueError("Invalid agent type")
    file_path = os.path.join(f"./sql_agents/{agent_type}", "prompt.txt")
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def is_text(content):
    """Check if the content is text and not empty"""
    if isinstance(content, str):
        if len(content) == 0:
            return False
    return True
