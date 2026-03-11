"""Helper utilities for adding telemetry spans to Azure SDK operations.

This module provides decorators and context managers for adding OpenTelemetry
spans to Azure SDK calls (CosmosDB, Blob Storage, etc.) without interfering
with Semantic Kernel's async generators.

Example usage:
    from common.telemetry.telemetry_helper import trace_operation

    @trace_operation("cosmosdb_query")
    async def query_items(self, query: str):
        # Your CosmosDB query here
        pass
"""

import asyncio
import functools
from contextlib import asynccontextmanager, contextmanager
from typing import Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


def get_tracer(name: str = __name__):
    """Get a tracer instance for the given name."""
    return trace.get_tracer(name)


def trace_operation(operation_name: str, attributes: Optional[dict] = None):
    """Decorator to add telemetry span to a function or method.

    Args:
        operation_name: Name of the operation for the span
        attributes: Optional dictionary of attributes to add to the span

    Example:
        @trace_operation("batch_processing", {"service": "sql_agents"})
        async def process_batch(batch_id: str):
            # Your code here
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(operation_name) as span:
                # Add custom attributes if provided
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))

                # Add function arguments as attributes (optional, for debugging)
                span.set_attribute("function", func.__name__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(operation_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))

                span.set_attribute("function", func.__name__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@asynccontextmanager
async def trace_context(operation_name: str, attributes: Optional[dict] = None):
    """Async context manager for adding telemetry span to a code block.

    Args:
        operation_name: Name of the operation for the span
        attributes: Optional dictionary of attributes to add to the span

    Example:
        async with trace_context("cosmosdb_batch_query", {"batch_id": batch_id}):
            results = await database.query_items(query)
            # Your code here
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(operation_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


@contextmanager
def trace_sync_context(operation_name: str, attributes: Optional[dict] = None):
    """Sync context manager for adding telemetry span to a code block.

    Args:
        operation_name: Name of the operation for the span
        attributes: Optional dictionary of attributes to add to the span

    Example:
        with trace_sync_context("blob_upload", {"file_name": file_name}):
            blob_client.upload_blob(data)
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(operation_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def add_span_attributes(attributes: dict):
    """Add attributes to the current span.

    Args:
        attributes: Dictionary of attributes to add

    Example:
        add_span_attributes({"user_id": user_id, "batch_id": batch_id})
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
