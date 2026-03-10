# Standard library
import logging
import os

# Third-party
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from dotenv import load_dotenv

load_dotenv()


def track_event_if_configured(event_name: str, event_data: dict):
    """Track a custom event using OpenTelemetry.
    
    This creates a span with the event name and adds the event data as attributes.
    The span will appear in Application Insights as a dependency with the event data.
    """
    instrumentation_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if instrumentation_key:
        try:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(f"event:{event_name}") as span:
                # Set span kind to internal for custom events
                span.set_attribute("event.name", event_name)
                span.set_attribute("event.type", "custom")
                
                # Add all event data as span attributes
                for key, value in event_data.items():
                    # Convert value to string to ensure it's serializable
                    span.set_attribute(f"event.{key}", str(value))
                
                # Add event to the span (appears in Application Insights)
                span.add_event(event_name, attributes=event_data)
                span.set_status(Status(StatusCode.OK))
                
                logging.debug(f"Tracked event: {event_name} with data: {event_data}")
        except Exception as e:
            logging.error(f"Failed to track event {event_name}: {e}")
    else:
        logging.warning(
            f"Skipping track_event for {event_name} as Application Insights is not configured"
        )
