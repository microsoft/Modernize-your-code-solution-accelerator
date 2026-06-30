from semantic_kernel.kernel_pydantic import KernelBaseModel


class FixerResponse(KernelBaseModel):
    """
    Model for the response of the fixer
    """

    thought: str
    fixed_query: str
    summary: str | None
