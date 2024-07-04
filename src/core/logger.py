import logging
from logging.handlers import BufferingHandler

from httpx import Client

from src.core.constants import settings


class SwitWebhookBufferingHandler(BufferingHandler):
    """ Add a webhook sender to the logger """
    def __init__(self, capacity: int = 999) -> None:
        super().__init__(capacity)

    def flush(self) -> None:
        if not self.buffer:
            return
        messages = [self.format(record) for record in self.buffer]
        if settings.SWIT_WEBHOOK_URL:
            payload = {"text": "\n".join(messages)}
            with Client() as client:
                client.post(settings.SWIT_WEBHOOK_URL, json=payload, timeout=10)
        else:
            print(messages)
        self.buffer.clear()

    def shouldFlush(self, record: logging.LogRecord) -> bool:
        """Swit webhook has a limit of 12,000 characters per message, so we flush"""
        messages = "\n".join([self.format(record) for record in self.buffer])
        if len(messages) >= 6000:
            return True
        return False


# Create a logger
provisioning_logger = logging.getLogger('ProvisioningLogger')
provisioning_logger.setLevel(logging.INFO)

# Create and add the stream handler to output to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
provisioning_logger.addHandler(console_handler)

# Add webhook handler
provisioning_logger.addHandler(SwitWebhookBufferingHandler())
