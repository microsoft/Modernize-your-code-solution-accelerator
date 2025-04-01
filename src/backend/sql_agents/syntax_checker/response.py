from typing import List

from semantic_kernel.kernel_pydantic import KernelBaseModel


class SyntaxErrorInt(KernelBaseModel):
    line: int
    column: int
    error: str


class SyntaxCheckerResponse(KernelBaseModel):
    """
    Response model for the syntax checker agent
    """

    thought: str
    syntax_errors: List[SyntaxErrorInt]
    summary: str
