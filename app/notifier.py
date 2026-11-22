"""Notifiers send messages to members. Both share one interface: send(to, subject, body)."""
import logging
import smtplib
from email.message import EmailMessage

log = logging.getLogger(__name__)


class ConsoleNotifier:
    """Default notifier for development: writes the message to the log."""

    def send(self, to, subject, body):
        log.info("To: %s | Subject: %s | %s", to, subject, body)


class SmtpNotifier:
    """Sends real email through an SMTP server (network dependency, mocked in tests)."""

    def __init__(self, host, port, sender):
        self.host, self.port, self.sender = host, port, sender

    def send(self, to, subject, body):
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self.host, self.port) as server:
            server.send_message(message)
