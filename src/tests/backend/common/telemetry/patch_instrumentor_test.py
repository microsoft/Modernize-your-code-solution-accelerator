"""Tests for common/telemetry/patch_instrumentor.py"""
import json
from unittest.mock import MagicMock, patch

import pytest

from common.telemetry.patch_instrumentor import (
    _fixed_response_to_str,
    _patch_fastapi_route_details,
    patch_instrumentors,
)


class TestFixedResponseToStr:
    def test_none_returns_none(self):
        assert _fixed_response_to_str(None) is None

    def test_str_returned_unchanged(self):
        assert _fixed_response_to_str("auto") == "auto"

    def test_empty_string_returned_unchanged(self):
        assert _fixed_response_to_str("") == ""

    def test_dict_returns_json_string(self):
        data = {"type": "json_object"}
        result = _fixed_response_to_str(data)
        assert result == json.dumps(data)

    def test_nested_dict_round_trips(self):
        data = {"type": "json_schema", "schema": {"name": "test"}}
        result = _fixed_response_to_str(data)
        assert json.loads(result) == data

    def test_integer_serialised_as_json(self):
        result = _fixed_response_to_str(42)
        assert result == "42"

    def test_list_serialised_as_json(self):
        data = [1, 2, 3]
        result = _fixed_response_to_str(data)
        assert result == json.dumps(data)

    def test_object_without_str_method_returns_string(self):
        class Custom:
            def __str__(self):
                return "custom_repr"

        result = _fixed_response_to_str(Custom())
        assert result is not None
        assert isinstance(result, str)


class TestPatchFastapiRouteDetails:
    def test_import_error_returns_silently(self):
        """ImportError on opentelemetry import causes an early return without raising."""
        import sys
        with patch.dict(sys.modules, {"opentelemetry.instrumentation.fastapi": None}):
            _patch_fastapi_route_details()  # must not raise

    def test_patches_attribute_when_modules_available(self):
        """When imports succeed, _get_route_details is replaced with a callable."""
        mock_instr = MagicMock()
        mock_instr._get_route_details = MagicMock()

        # We need Match to exist on the mocked starlette.routing module
        from starlette.routing import Match
        mock_starlette = MagicMock()
        mock_starlette.Match = Match

        import sys
        original_instr = sys.modules.get("opentelemetry.instrumentation.fastapi")
        sys.modules["opentelemetry.instrumentation.fastapi"] = mock_instr

        try:
            _patch_fastapi_route_details()
            assert callable(mock_instr._get_route_details)
        finally:
            if original_instr is None:
                sys.modules.pop("opentelemetry.instrumentation.fastapi", None)
            else:
                sys.modules["opentelemetry.instrumentation.fastapi"] = original_instr

    def test_exception_inside_try_does_not_propagate(self):
        """Exceptions inside the patch block are caught and logged, not raised."""
        import sys

        class ReadOnlyModule:
            def __setattr__(self, name, value):
                raise AttributeError(f"read-only: {name}")

        original = sys.modules.get("opentelemetry.instrumentation.fastapi")
        sys.modules["opentelemetry.instrumentation.fastapi"] = ReadOnlyModule()
        try:
            _patch_fastapi_route_details()  # must not raise
        finally:
            if original is not None:
                sys.modules["opentelemetry.instrumentation.fastapi"] = original
            else:
                sys.modules.pop("opentelemetry.instrumentation.fastapi", None)


class TestPatchInstrumentors:
    def test_agents_instrumentor_patched_when_available(self):
        mock_cls = MagicMock()
        mock_cls.agent_api_response_to_str = None

        mock_agents_telemetry = MagicMock()
        mock_agents_telemetry._AIAgentsInstrumentorPreview = mock_cls

        with patch.dict(
            "sys.modules",
            {
                "azure.ai.agents.telemetry._ai_agents_instrumentor": mock_agents_telemetry,
            },
        ):
            with patch(
                "common.telemetry.patch_instrumentor._patch_fastapi_route_details"
            ) as mock_patch_routes:
                patch_instrumentors()
                mock_patch_routes.assert_called_once()

    def test_agents_import_error_handled_gracefully(self):
        """If azure.ai.agents is absent, patch_instrumentors completes without error."""
        with patch(
            "common.telemetry.patch_instrumentor._patch_fastapi_route_details"
        ) as mock_patch_routes:
            # Ensure the import attempt fails
            original = __import__

            def selective_import(name, *args, **kwargs):
                if "azure.ai.agents" in name or "azure.ai.projects" in name:
                    raise ImportError(f"mocked: {name}")
                return original(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=selective_import):
                patch_instrumentors()

            mock_patch_routes.assert_called_once()

    def test_projects_import_error_handled_gracefully(self):
        """If azure.ai.projects is absent the function still completes."""
        with patch(
            "common.telemetry.patch_instrumentor._patch_fastapi_route_details"
        ):
            patch_instrumentors()  # real imports attempted; ImportError caught internally

    def test_patch_fastapi_route_details_always_called(self):
        """_patch_fastapi_route_details is invoked regardless of agent import outcome."""
        with patch(
            "common.telemetry.patch_instrumentor._patch_fastapi_route_details"
        ) as mock_fn:
            patch_instrumentors()
        mock_fn.assert_called_once()
