"""SQL semantic verifier response models"""

from semantic_kernel.kernel_pydantic import KernelBaseModel


class SemanticVerifierResponse(KernelBaseModel):
    """
    Model for the response of the semantic verifier agent
    """

    judgement: str
    differences: list[str]
    summary: str
