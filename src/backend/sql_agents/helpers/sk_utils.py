"""Kernel mixin for creating a kernel with chat completion service."""

import logging
import os

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.kernel import Kernel

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_kernel_with_chat_completion(
    service_id: str, deployment_name: str = None
) -> Kernel:
    """Create a kernel with chat completion service."""
    kernel = Kernel()
    if deployment_name is None:
        try:
            deployment_name = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
        except KeyError as e:
            logger.error("deployment_name is required.")
            raise ValueError("deployment_name is required.") from e
    try:
        kernel.add_service(
            AzureChatCompletion(deployment_name=deployment_name, service_id=service_id)
        )
    except Exception as exc:
        logger.error("Failed to add chat completion service.")
        raise ValueError("Failed to add chat completion service.") from exc
    return kernel
