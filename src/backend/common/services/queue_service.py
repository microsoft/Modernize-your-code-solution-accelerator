import asyncio
import json

from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient
from common.config.config import Config
from common.logger.app_logger import AppLogger
from azure.identity.aio import DefaultAzureCredential


class QueueService:
    def __init__(self):
        self.logger = AppLogger("QueueService")
        config = Config()

        self.queue_name = config.azure_queue_name
        self.azure_service_bus_namespace = config.azure_service_bus_namespace
        try:
            self.azure_credentials = DefaultAzureCredential()

        except Exception as e:
            self.logger.info(
                f"Managed identity not available, using DefaultAzureCredential: {e}"
            )
            self.azure_credentials = DefaultAzureCredential()

        self.servicebus_client = ServiceBusClient(
            fully_qualified_namespace=self.azure_service_bus_namespace,
            credential=self.azure_credentials,
        )

    async def send_message_to_queue(self, message: dict):
        """Send a message to the Azure Service Bus Queue."""
        try:
            async with self.servicebus_client:
                self.logger.info(f"Sending message: {message}")
                self.logger.info(f"Queue name: {self.queue_name}")
                sender = self.servicebus_client.get_queue_sender(
                    queue_name=self.queue_name
                )
                async with sender:
                    servicebus_message = ServiceBusMessage(json.dumps(message))
                    await sender.send_messages(servicebus_message)
                    self.logger.info(f"Sent message: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise

    async def receive_messages_from_queue(self, max_messages: int = 1):
        """Receive messages from the Azure Service Bus Queue."""
        messages_received = []
        try:
            async with self.servicebus_client:
                receiver = self.servicebus_client.get_queue_receiver(
                    queue_name=self.queue_name, max_wait_time=5
                )
                async with receiver:
                    received_messages = await receiver.receive_messages(
                        max_message_count=max_messages
                    )
                    for message in received_messages:
                        messages_received.append(json.loads(str(message)))
                        await receiver.complete_message(
                            message
                        )  # Mark message as processed
        except Exception as e:
            self.logger.error(f"Failed to receive messages: {e}")
            raise
        return messages_received

    async def purge_queue(self):
        """Purges all messages from the Azure Service Bus Queue."""
        try:
            async with self.servicebus_client:
                receiver = self.servicebus_client.get_queue_receiver(
                    queue_name=self.queue_name
                )
                async with receiver:
                    received_messages = await receiver.receive_messages(
                        max_message_count=100
                    )
                    while received_messages:
                        for message in received_messages:
                            await receiver.complete_message(message)
                        received_messages = await receiver.receive_messages(
                            max_message_count=100
                        )
                    self.logger.info("Queue purged successfully.")
        except Exception as e:
            self.logger.error(f"Failed to purge queue: {e}")
            raise
