from semantic_kernel.kernel_pydantic import KernelBaseModel


class MigratorCandidate(KernelBaseModel):
    """
    Model for a single candidate for migration
    """

    plan: str
    candidate_query: str


class MigratorResponse(KernelBaseModel):
    """
    Model for the response of the migrator
    """

    input_summary: str
    candidates: list[MigratorCandidate]
    input_error: str | None = None
    summary: str | None = None
    rai_error: str | None = None
