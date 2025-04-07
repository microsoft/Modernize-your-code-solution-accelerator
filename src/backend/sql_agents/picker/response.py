from pydantic import BaseModel


class PickerCandidateSummary(BaseModel):
    candidate_index: int
    candidate_summary: str


class PickerResponse(BaseModel):
    """The response of the picker agent."""

    source_summary: str
    candidate_summaries: list[PickerCandidateSummary]
    conclusion: str
    picked_query: str
    summary: str | None
