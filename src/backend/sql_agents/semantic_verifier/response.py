from semantic_kernel.kernel_pydantic import KernelBaseModel


class SemanticVerifierResponse(KernelBaseModel):
    """
    Response model for the semantic verifier agent
    """

    analysis: str
    judgement: str
    differences: list[str]
    summary: str | None

    def __str__(self):
        return f"Analysis: {self.analysis}\nJudgement: {self.judgement}\nDifferences: {self.differences}\nSummary: {self.summary}"
