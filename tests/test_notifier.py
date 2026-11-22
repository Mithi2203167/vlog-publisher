import logging
from unittest.mock import patch

from app.notifier import ConsoleNotifier, SmtpNotifier


def test_smtp_notifier_builds_and_sends_message():
    # The network is mocked: no real mail server is contacted.
    with patch("app.notifier.smtplib.SMTP") as smtp:
        SmtpNotifier("smtp.example.com", 587, "club@example.com").send("a@x.com", "Hi", "Body")

    smtp.assert_called_once_with("smtp.example.com", 587)
    server = smtp.return_value.__enter__.return_value
    server.send_message.assert_called_once()
    message = server.send_message.call_args[0][0]
    assert message["To"] == "a@x.com"
    assert message["From"] == "club@example.com"
    assert message["Subject"] == "Hi"


def test_console_notifier_logs_message(caplog):
    with caplog.at_level(logging.INFO):
        ConsoleNotifier().send("a@x.com", "Hi", "Body")
    assert "a@x.com" in caplog.text
