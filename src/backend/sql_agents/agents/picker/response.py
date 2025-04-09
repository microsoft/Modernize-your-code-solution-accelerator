from semantic_kernel.kernel_pydantic import KernelBaseModel


class PickerResponse(KernelBaseModel):
    """
    The response of the picker agent.
    """

    conclusion: str
    picked_query: str
    summary: str | None
