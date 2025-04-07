import base64
import json
import logging
from typing import Dict

from api.auth.sample_user import sample_user

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class UserDetails:
    def __init__(self, user_details: Dict):
        self.user_principal_id = user_details.get("user_principal_id")
        self.user_name = user_details.get("user_name")
        self.auth_provider = user_details.get("auth_provider")
        self.auth_token = user_details.get("auth_token")
        self.tenant_id = None

        # Get tenant ID if client principal exists
        client_principal_b64 = user_details.get("client_principal_b64")
        if (
            client_principal_b64
            and client_principal_b64 != "your_base_64_encoded_token"
        ):
            self.tenant_id = get_tenant_id(client_principal_b64)


def get_tenant_id(client_principal_b64: str) -> str:
    """Extract tenant ID from base64 encoded client principal."""
    try:
        decoded_bytes = base64.b64decode(client_principal_b64)
        decoded_string = decoded_bytes.decode("utf-8")
        user_info = json.loads(decoded_string)
        return user_info.get("tid", "")
    except Exception :
        logger.exception("Error decoding client principal")
        return ""


def get_authenticated_user(request: Request) -> UserDetails:
    """Get authenticated user details from request headers."""
    user_object = {}
    headers = dict(request.headers)
    # Check if we're in production with real headers
    if "x-ms-client-principal-id" not in headers:
        logger.info("No user principal found in headers - using development user")
        # Use sample user for development
        raw_user_object = sample_user
    else:
        raw_user_object = headers

    # Normalize headers to lowercase
    normalized_headers = {k.lower(): v for k, v in raw_user_object.items()}

    # Extract user details
    user_object = {
        "user_principal_id": normalized_headers.get("x-ms-client-principal-id"),
    }
    logger.info(f"User object princial id: {user_object['user_principal_id']}")
    if not user_object["user_principal_id"]:
        raise HTTPException(status_code=401, detail="User not authenticated")

    return UserDetails(user_object)
