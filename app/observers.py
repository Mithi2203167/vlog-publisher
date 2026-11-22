"""Observer pattern: modules publish what happened; observers react without the modules knowing."""
import logging

log = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, topic, observer):
        self._subscribers.setdefault(topic, []).append(observer)

    def publish(self, topic, payload):
        for observer in self._subscribers.get(topic, []):
            try:
                observer(payload)
            except Exception:  # one broken observer must not stop the others
                log.exception("observer failed for topic %s", topic)


class EmailNotificationObserver:
    def __init__(self, notifier, recipients, formatter):
        self.notifier = notifier
        self.recipients = recipients  # anything with all_emails()
        self.formatter = formatter

    def __call__(self, payload):
        subject, body = self.formatter(payload)
        for email in self.recipients.all_emails():
            try:
                self.notifier.send(email, subject, body)
            except Exception:
                log.exception("could not notify %s", email)


def format_post(post):
    return (f"New {post.kind}: {post.title}", f"A new {post.kind} was published: {post.title}")
