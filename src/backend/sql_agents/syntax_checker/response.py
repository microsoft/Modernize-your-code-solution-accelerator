from typing import List

from pydantic import BaseModel


class SyntaxErrorInt(BaseModel):
    line: int
    column: int
    error: str


class SyntaxCheckerResponse(BaseModel):
    """Response model for the syntax checker agent."""

    thought: str
    syntax_errors: List[SyntaxErrorInt]
    summary: str
