import json
import logging
import requests
import os
from azure.servicebus import ServiceBusMessage
from azure.functions import ServiceBusMessage as FunctionServiceBusMessage


def main(msg: FunctionServiceBusMessage):
    """
    This function gets triggered whenever a new message arrives on the Service Bus Queue.
    The message is automatically passed in as 'msg'.
    """
    logging.info("Python ServiceBus queue trigger processed a message.")

    # Message body is bytes, decode to string
    raw_message = msg.get_body().decode("utf-8")

    # Convert string to dictionary
    message_dict = json.loads(raw_message)

    # Now call your FastAPI endpoint with that message
    # e.g., "http://yourfastapi/queue-callback"
    api_url = os.getenv(
        "API_QUEUE_CALLBACK_URL"
    )  # e.g. https://your-api.com/queue-callback
    try:
        response = requests.post(api_url, json=message_dict)
        response.raise_for_status()
        logging.info("Message successfully forwarded to FastAPI endpoint.")
    except Exception as ex:
        logging.error(f"Failed to POST message to {api_url}. Error: {ex}")
