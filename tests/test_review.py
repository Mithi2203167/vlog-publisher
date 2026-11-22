from unittest.mock import Mock

import pytest

from app.posts import Post
from app.review import ManualReview, ReviewService, TrustedAuthorPolicy


def make_post(status="draft"):
    return Post(1, "article", "Why Git?", "Version control keeps a history.", None, 7, status)


def make_service(post, policy=None, published_count=0):
    repo, bus = Mock(), Mock()
    repo.get.return_value = post
    repo.published_count.return_value = published_count
    return ReviewService(repo, policy or ManualReview(), bus), repo, bus


# ---- Strategy pattern: review policies --------------------------------------
def test_manual_review_always_sends_to_pending():
    policy = ManualReview()
    assert policy.decide(0) == "pending"
    assert policy.decide(50) == "pending"


def test_trusted_policy_publishes_after_enough_published_posts():
    policy = TrustedAuthorPolicy(min_published=2)
    assert policy.decide(1) == "pending"
    assert policy.decide(2) == "published"


# ---- Submit ---------------------------------------------------------------
def test_submit_with_manual_review_goes_pending():
    service, repo, bus = make_service(make_post())
    result = service.submit(1)
    assert result.status == "pending"
    repo.set_status.assert_called_once_with(1, "pending")
    bus.publish.assert_not_called()


def test_submit_by_trusted_author_publishes_and_notifies():
    service, repo, bus = make_service(make_post(), TrustedAuthorPolicy(2), published_count=3)
    result = service.submit(1)
    assert result.status == "published"
    repo.set_status.assert_called_once_with(1, "published")
    bus.publish.assert_called_once_with("post.published", result)


@pytest.mark.parametrize("status", ["pending", "published", "rejected"])
def test_only_drafts_can_be_submitted(status):
    service, repo, _ = make_service(make_post(status))
    with pytest.raises(ValueError):
        service.submit(1)
    repo.set_status.assert_not_called()


# ---- Approve --------------------------------------------------------------
def test_approve_publishes_and_notifies():
    service, repo, bus = make_service(make_post("pending"))
    result = service.approve(1)
    assert result.status == "published"
    repo.set_status.assert_called_once_with(1, "published")
    bus.publish.assert_called_once_with("post.published", result)


@pytest.mark.parametrize("status", ["draft", "published", "rejected"])
def test_only_pending_posts_can_be_approved(status):
    service, repo, bus = make_service(make_post(status))
    with pytest.raises(ValueError):
        service.approve(1)
    repo.set_status.assert_not_called()
    bus.publish.assert_not_called()


# ---- Reject ---------------------------------------------------------------
def test_reject_needs_a_reason():
    service, repo, _ = make_service(make_post("pending"))
    with pytest.raises(ValueError):
        service.reject(1, "  ")
    repo.set_status.assert_not_called()


def test_reject_stores_reason_and_does_not_notify():
    service, repo, bus = make_service(make_post("pending"))
    result = service.reject(1, "Too short")
    assert result.status == "rejected"
    assert result.reason == "Too short"
    repo.set_status.assert_called_once_with(1, "rejected", "Too short")
    bus.publish.assert_not_called()


def test_only_pending_posts_can_be_rejected():
    service, _, _ = make_service(make_post("published"))
    with pytest.raises(ValueError):
        service.reject(1, "Late")


def test_missing_post_raises_lookup_error():
    service, repo, _ = make_service(None)
    with pytest.raises(LookupError):
        service.approve(99)
