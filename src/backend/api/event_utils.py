# Standard library
import logging
import os

# Third-party
from applicationinsights import TelemetryClient
from applicationinsights.channel import SynchronousQueue, SynchronousSender, TelemetryChannel

from dotenv import load_dotenv

load_dotenv()

# Global telemetry client (initialized once)
_telemetry_client = None


def _get_telemetry_client():
    """Get or create the Application Insights telemetry client."""
    global _telemetry_client

    if _telemetry_client is None:
        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if connection_string:
            try:
                # Extract instrumentation key from connection string
                # Format: InstrumentationKey=xxx;IngestionEndpoint=https://...
                parts = dict(part.split('=', 1) for part in connection_string.split(';') if '=' in part)
                instrumentation_key = parts.get('InstrumentationKey')

                if instrumentation_key:
                    # Create a synchronous channel for immediate sending
                    sender = SynchronousSender()
                    queue = SynchronousQueue(sender)
                    channel = TelemetryChannel(None, queue)

                    _telemetry_client = TelemetryClient(instrumentation_key, channel)
                    logging.info("Application Insights TelemetryClient initialized successfully")
                else:
                    logging.error("Could not extract InstrumentationKey from connection string")
            except Exception as e:
                logging.error(f"Failed to initialize TelemetryClient: {e}")

    return _telemetry_client


def track_event_if_configured(event_name: str, event_data: dict):
    """Track a custom event to Application Insights customEvents table.

    This uses the Application Insights SDK TelemetryClient which properly
    sends custom events to the customEvents table in Application Insights.
    """
    instrumentation_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if instrumentation_key:
        try:
            client = _get_telemetry_client()
            if client:
                # Convert all values to strings to ensure compatibility
                properties = {k: str(v) for k, v in event_data.items()}

                # Track the custom event
                client.track_event(event_name, properties=properties)
                client.flush()  # Ensure immediate sending

                logging.debug(f"Tracked custom event: {event_name} with data: {event_data}")
            else:
                logging.warning("TelemetryClient not available, custom event not tracked")
        except Exception as e:
            logging.error(f"Failed to track event {event_name}: {e}")
    else:
        logging.warning(
            f"Skipping track_event for {event_name} as Application Insights is not configured"
        )
