from pydantic import BaseModel


class SemanticVerifierResponse(BaseModel):
    """
    Response model for the semantic verifier agent
    """

    analysis: str
    judgement: str
    differences: list[str]
    summary: str | None

    def __str__(self):
        return f"Analysis: {self.analysis}\nJudgement: {self.judgement}\nDifferences: {self.differences}\nSummary: {self.summary}"
