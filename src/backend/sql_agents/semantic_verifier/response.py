from semantic_kernel.kernel_pydantic import KernelBaseModel


class SemanticVerifierResponse(KernelBaseModel):
    """
    Response model for the semantic verifier agent
    Args:
        analysis (str): The analysis of the SQL query.
        judgement (str): The judgement of the SQL query.
        differences (list[str]): List of differences found in the SQL query.
        summary (str): A one sentence summary of the response.
    """

    analysis: str
    judgement: str
    differences: list[str]
    summary: str | None
