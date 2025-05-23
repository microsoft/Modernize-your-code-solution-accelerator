import base64
import json
from unittest.mock import MagicMock

from api.auth.auth_utils import UserDetails, get_authenticated_user, get_tenant_id

from fastapi import HTTPException, Request

import pytest


def test_get_tenant_id_valid():
    payload = {"tid": "tenant123"}
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

    result = get_tenant_id(encoded)
    assert result == "tenant123"


def test_get_tenant_id_invalid():
    invalid_b64 = "invalid_base64_string"
    result = get_tenant_id(invalid_b64)
    assert result == ""


def test_user_details_initialization_with_tenant():
    payload = {"tid": "tenant456"}
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

    user_data = {
        "user_principal_id": "user1",
        "user_name": "John Doe",
        "auth_provider": "aad",
        "auth_token": "fake_token",
        "client_principal_b64": encoded,
    }

    user = UserDetails(user_data)
    assert user.user_principal_id == "user1"
    assert user.user_name == "John Doe"
    assert user.tenant_id == "tenant456"


def test_user_details_initialization_without_tenant():
    user_data = {
        "user_principal_id": "user2",
        "user_name": "Jane Doe",
        "auth_provider": "aad",
        "auth_token": "fake_token",
        "client_principal_b64": "your_base_64_encoded_token",
    }

    user = UserDetails(user_data)
    assert user.tenant_id is None


def test_get_authenticated_user_valid():
    headers = {
        "x-ms-client-principal-id": "user3",
    }

    mock_request = MagicMock(spec=Request)
    mock_request.headers = headers

    user = get_authenticated_user(mock_request)
    assert isinstance(user, UserDetails)
    assert user.user_principal_id == "user3"


def test_get_authenticated_user_raises_http_exception(monkeypatch):
    # Mocking a development environment with no user principal in sample_user
    sample_user_mock = {"some-header": "some-value"}

    monkeypatch.setattr("api.auth.auth_utils.sample_user", sample_user_mock)

    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    with pytest.raises(HTTPException) as exc_info:
        get_authenticated_user(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not authenticated"
