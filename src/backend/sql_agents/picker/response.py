from semantic_kernel.kernel_pydantic import KernelBaseModel


class PickerCandidateSummary(KernelBaseModel):
    candidate_index: int
    candidate_summary: str


class PickerResponse(KernelBaseModel):
    """
    The response of the picker agent.
    """

    source_summary: str
    candidate_summaries: list[PickerCandidateSummary]
    conclusion: str
    picked_query: str
    summary: str | None
