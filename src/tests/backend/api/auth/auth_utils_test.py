"""Tests for auth_utils module."""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.api.auth.auth_utils import (
    UserDetails,
    get_tenant_id,
    get_authenticated_user,
)


class TestUserDetails:
    """Tests for UserDetails class."""

    def test_user_details_initialization(self):
        """Test UserDetails initialization with basic data."""
        user_data = {
            "user_principal_id": "test-user-id",
            "user_name": "Test User",
            "auth_provider": "azure",
            "auth_token": "test-token",
        }
        
        user = UserDetails(user_data)
        
        assert user.user_principal_id == "test-user-id"
        assert user.user_name == "Test User"
        assert user.auth_provider == "azure"
        assert user.auth_token == "test-token"
        assert user.tenant_id is None

    def test_user_details_with_client_principal(self):
        """Test UserDetails initialization with client principal."""
        tenant_id = "test-tenant-id"
        client_principal = base64.b64encode(
            json.dumps({"tid": tenant_id}).encode()
        ).decode()
        
        user_data = {
            "user_principal_id": "test-user-id",
            "client_principal_b64": client_principal,
        }
        
        user = UserDetails(user_data)
        
        assert user.user_principal_id == "test-user-id"
        assert user.tenant_id == tenant_id

    def test_user_details_with_placeholder_principal(self):
        """Test UserDetails with placeholder client principal."""
        user_data = {
            "user_principal_id": "test-user-id",
            "client_principal_b64": "your_base_64_encoded_token",
        }
        
        user = UserDetails(user_data)
        
        assert user.tenant_id is None

    def test_user_details_missing_fields(self):
        """Test UserDetails with missing fields."""
        user_data = {}
        
        user = UserDetails(user_data)
        
        assert user.user_principal_id is None
        assert user.user_name is None
        assert user.auth_provider is None


class TestGetTenantId:
    """Tests for get_tenant_id function."""

    def test_get_tenant_id_success(self):
        """Test successful tenant ID extraction."""
        tenant_id = "my-tenant-id"
        encoded = base64.b64encode(json.dumps({"tid": tenant_id}).encode()).decode()
        
        result = get_tenant_id(encoded)
        
        assert result == tenant_id

    def test_get_tenant_id_missing_tid(self):
        """Test extraction when tid is missing."""
        encoded = base64.b64encode(json.dumps({"other": "data"}).encode()).decode()
        
        result = get_tenant_id(encoded)
        
        assert result == ""

    def test_get_tenant_id_invalid_base64(self):
        """Test extraction with invalid base64."""
        result = get_tenant_id("not-valid-base64!!!")
        
        assert result == ""

    def test_get_tenant_id_invalid_json(self):
        """Test extraction with invalid JSON."""
        encoded = base64.b64encode(b"not valid json").decode()
        
        result = get_tenant_id(encoded)
        
        assert result == ""


class TestGetAuthenticatedUser:
    """Tests for get_authenticated_user function."""

    def test_get_authenticated_user_from_headers(self):
        """Test getting user from request headers."""
        request = MagicMock()
        request.headers = {
            "x-ms-client-principal-id": "test-user-id",
            "x-ms-client-principal-name": "Test User",
        }
        
        user = get_authenticated_user(request)
        
        assert user.user_principal_id == "test-user-id"

    def test_get_authenticated_user_development_mode(self):
        """Test getting user in development mode (no headers)."""
        request = MagicMock()
        request.headers = {}
        
        with patch("backend.api.auth.auth_utils.sample_user", {"x-ms-client-principal-id": "dev-user"}):
            user = get_authenticated_user(request)
            
            assert user.user_principal_id == "dev-user"

    def test_get_authenticated_user_no_principal_id(self):
        """Test error when no principal ID."""
        request = MagicMock()
        request.headers = {
            "x-ms-client-principal-id": None,
        }
        
        # When sample_user also doesn't have ID
        with patch("backend.api.auth.auth_utils.sample_user", {}):
            with pytest.raises(HTTPException) as exc_info:
                get_authenticated_user(request)
            assert exc_info.value.status_code == 401

    def test_get_authenticated_user_mixed_case_headers(self):
        """Test getting user with mixed case headers - falls back to sample_user since header check is case-sensitive."""
        request = MagicMock()
        # The function checks for lowercase header, so uppercase won't match
        request.headers = {
            "X-MS-CLIENT-PRINCIPAL-ID": "test-user-id",
        }
        
        # Since x-ms-client-principal-id (lowercase) is not in headers, it uses sample_user
        with patch("backend.api.auth.auth_utils.sample_user", {"x-ms-client-principal-id": "sample-user-id"}):
            user = get_authenticated_user(request)
            # Headers are normalized but the initial check is case-sensitive
            assert user.user_principal_id == "sample-user-id"
