from unittest.mock import Mock

from app.observers import EmailNotificationObserver, EventBus, format_post
from app.posts import Post


def test_bus_delivers_only_to_topic_subscribers():
    bus, received = EventBus(), []
    bus.subscribe("a", received.append)
    bus.publish("a", 1)
    bus.publish("b", 2)
    assert received == [1]


def test_bus_isolates_a_failing_observer():
    bus, received = EventBus(), []

    def broken(payload):
        raise RuntimeError("boom")

    bus.subscribe("a", broken)
    bus.subscribe("a", received.append)
    bus.publish("a", 1)
    assert received == [1]


def test_email_observer_sends_to_every_recipient():
    notifier, recipients = Mock(), Mock()
    recipients.all_emails.return_value = ["a@x.com", "b@x.com"]
    observer = EmailNotificationObserver(notifier, recipients, lambda p: ("New post", f"{p} is live"))

    observer("Why Git?")

    assert notifier.send.call_count == 2
    notifier.send.assert_any_call("a@x.com", "New post", "Why Git? is live")


def test_email_observer_continues_after_one_send_fails():
    notifier, recipients = Mock(), Mock()
    recipients.all_emails.return_value = ["a@x.com", "b@x.com"]
    notifier.send.side_effect = [RuntimeError("smtp down"), None]
    observer = EmailNotificationObserver(notifier, recipients, lambda p: ("S", "B"))

    observer("x")

    assert notifier.send.call_count == 2


def test_format_post_names_kind_and_title():
    post = Post(1, "vlog", "Orientation day", None, "https://youtu.be/abc", 1, "published")
    subject, body = format_post(post)
    assert "vlog" in subject and "Orientation day" in subject
    assert "Orientation day" in body
