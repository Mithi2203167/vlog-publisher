import pytest

from app.subscriptions import SubscriberRepository, SubscriptionService


def make_service(conn):
    return SubscriptionService(SubscriberRepository(conn))


def test_subscribe_normalizes_email(conn):
    assert make_service(conn).subscribe("  Reader@X.com ") == "reader@x.com"


@pytest.mark.parametrize("email", ["", "nope", "a@x"])
def test_subscribe_rejects_invalid_email(conn, email):
    with pytest.raises(ValueError):
        make_service(conn).subscribe(email)


def test_duplicate_subscription_is_rejected(conn):
    service = make_service(conn)
    service.subscribe("reader@x.com")
    with pytest.raises(ValueError):
        service.subscribe("READER@x.com")


def test_unsubscribe_removes_the_email(conn):
    service = make_service(conn)
    service.subscribe("reader@x.com")
    service.unsubscribe("reader@x.com")
    assert service.list() == []


def test_unsubscribe_unknown_email_raises_lookup_error(conn):
    with pytest.raises(LookupError):
        make_service(conn).unsubscribe("ghost@x.com")


def test_list_returns_all_subscribers(conn):
    service = make_service(conn)
    service.subscribe("a@x.com")
    service.subscribe("b@x.com")
    assert service.list() == ["a@x.com", "b@x.com"]
