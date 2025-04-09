"""SQL Syntax Checker Response Models"""

from typing import List

from semantic_kernel.kernel_pydantic import KernelBaseModel


class SyntaxErrorInt(KernelBaseModel):
    """
    Model for syntax error details
    Args:
        line (int): Line number where the error occurred.
        column (int): Column number where the error occurred.
        error (str): Description of the syntax error.
    """

    line: int
    column: int
    error: str


class SyntaxCheckerResponse(KernelBaseModel):
    """
    Response model for the syntax checker agent
    Args:
        thought (str): Thought process of the agent.
        syntax_errors (List[SyntaxErrorInt]): List of syntax errors found in the SQL query.
        summary (str): One line summary of the agent's response.
    """

    thought: str
    syntax_errors: List[SyntaxErrorInt]
    summary: str
