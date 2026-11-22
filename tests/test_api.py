from unittest.mock import Mock

import pytest

from app.api import create_app
from app.review import TrustedAuthorPolicy

LONG_BODY = "Version control keeps a history of every change."


@pytest.fixture
def ctx():
    notifier = Mock()
    app = create_app({"DATABASE": ":memory:", "NOTIFIER": notifier})
    return app.test_client(), notifier

def test_list_subscriptions(ctx):
    client, _ = ctx
    client.post("/subscriptions", json={"email": "reader@x.com"})
    assert client.get("/subscriptions").get_json() == ["reader@x.com"]
    
def make_author(client, email="rafi@ruet.ac.bd"):
    return client.post("/authors", json={"name": "Rafi", "email": email}).get_json()


def make_article(client, author_id, title="Why Git?"):
    return client.post(
        "/posts", json={"kind": "article", "author_id": author_id, "title": title, "body": LONG_BODY}
    )


def test_register_author_and_reject_duplicate(ctx):
    client, _ = ctx
    assert client.post("/authors", json={"name": "Rafi", "email": "r@x.com"}).status_code == 201
    duplicate = client.post("/authors", json={"name": "Other", "email": "r@x.com"})
    assert duplicate.status_code == 400
    assert "error" in duplicate.get_json()


def test_list_authors(ctx):
    client, _ = ctx
    make_author(client)
    assert len(client.get("/authors").get_json()) == 1


def test_create_article_draft(ctx):
    client, _ = ctx
    author = make_author(client)
    response = make_article(client, author["id"])
    assert response.status_code == 201
    assert response.get_json()["status"] == "draft"


def test_vlog_without_video_url_is_rejected(ctx):
    client, _ = ctx
    author = make_author(client)
    response = client.post("/posts", json={"kind": "vlog", "author_id": author["id"], "title": "Day 1"})
    assert response.status_code == 400


def test_unknown_author_is_rejected(ctx):
    client, _ = ctx
    assert make_article(client, 999).status_code == 400


def test_publish_flow_notifies_subscribers(ctx):
    client, notifier = ctx
    client.post("/subscriptions", json={"email": "reader@x.com"})
    author = make_author(client)
    post = make_article(client, author["id"]).get_json()

    assert client.post(f"/posts/{post['id']}/submit").get_json()["status"] == "pending"
    notifier.send.assert_not_called()

    assert client.post(f"/posts/{post['id']}/approve").get_json()["status"] == "published"
    notifier.send.assert_called_once()
    assert notifier.send.call_args[0][0] == "reader@x.com"
    assert len(client.get("/posts?status=published").get_json()) == 1


def test_reject_flow_stores_reason(ctx):
    client, notifier = ctx
    author = make_author(client)
    post = make_article(client, author["id"]).get_json()
    client.post(f"/posts/{post['id']}/submit")
    result = client.post(f"/posts/{post['id']}/reject", json={"reason": "Too short"}).get_json()
    assert result["status"] == "rejected"
    assert result["reason"] == "Too short"
    notifier.send.assert_not_called()


def test_reject_without_reason_is_400(ctx):
    client, _ = ctx
    author = make_author(client)
    post = make_article(client, author["id"]).get_json()
    client.post(f"/posts/{post['id']}/submit")
    assert client.post(f"/posts/{post['id']}/reject", json={}).status_code == 400


def test_cannot_approve_a_draft(ctx):
    client, _ = ctx
    author = make_author(client)
    post = make_article(client, author["id"]).get_json()
    assert client.post(f"/posts/{post['id']}/approve").status_code == 400


def test_trusted_policy_publishes_on_submit():
    notifier = Mock()
    app = create_app(
        {"DATABASE": ":memory:", "NOTIFIER": notifier, "REVIEW_POLICY": TrustedAuthorPolicy(min_published=0)}
    )
    client = app.test_client()
    client.post("/subscriptions", json={"email": "reader@x.com"})
    author = make_author(client)
    post = make_article(client, author["id"]).get_json()
    assert client.post(f"/posts/{post['id']}/submit").get_json()["status"] == "published"
    notifier.send.assert_called_once()


def test_comments_only_on_published_posts(ctx):
    client, _ = ctx
    author = make_author(client)
    post = make_article(client, author["id"]).get_json()
    url = f"/posts/{post['id']}/comments"
    assert client.post(url, json={"name": "Nusrat", "text": "Nice"}).status_code == 400

    client.post(f"/posts/{post['id']}/submit")
    client.post(f"/posts/{post['id']}/approve")
    assert client.post(url, json={"name": "Nusrat", "text": "Nice"}).status_code == 201
    assert [c["text"] for c in client.get(url).get_json()] == ["Nice"]


def test_subscribe_and_unsubscribe(ctx):
    client, _ = ctx
    assert client.post("/subscriptions", json={"email": "reader@x.com"}).status_code == 201
    assert client.post("/subscriptions", json={"email": "reader@x.com"}).status_code == 400
    assert client.delete("/subscriptions", json={"email": "reader@x.com"}).status_code == 200
    assert client.delete("/subscriptions", json={"email": "reader@x.com"}).status_code == 404


def test_missing_post_is_404(ctx):
    client, _ = ctx
    assert client.get("/posts/999").status_code == 404
    assert client.post("/posts/999/submit").status_code == 404
