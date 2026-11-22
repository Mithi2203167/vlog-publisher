"""Review module. Uses the Strategy pattern: the review policy decides what happens on submit."""
from dataclasses import replace


class ManualReview:
    """Every submitted post waits for an editor."""

    def decide(self, published_count):
        return "pending"


class TrustedAuthorPolicy:
    """Authors with enough published posts are published immediately; others wait for an editor."""

    def __init__(self, min_published=2):
        self.min_published = min_published

    def decide(self, published_count):
        return "published" if published_count >= self.min_published else "pending"


class ReviewService:
    def __init__(self, post_repo, policy, bus):
        self.repo = post_repo
        self.policy = policy
        self.bus = bus

    def submit(self, post_id):
        post = self._get(post_id)
        if post.status != "draft":
            raise ValueError(f"only drafts can be submitted (this post is {post.status})")
        status = self.policy.decide(self.repo.published_count(post.author_id))
        self.repo.set_status(post_id, status)
        updated = replace(post, status=status)
        if status == "published":
            self.bus.publish("post.published", updated)
        return updated

    def approve(self, post_id):
        post = self._pending(post_id)
        self.repo.set_status(post_id, "published")
        updated = replace(post, status="published")
        self.bus.publish("post.published", updated)
        return updated

    def reject(self, post_id, reason):
        if not reason or not reason.strip():
            raise ValueError("a reason is required to reject a post")
        post = self._pending(post_id)
        reason = reason.strip()
        self.repo.set_status(post_id, "rejected", reason)
        return replace(post, status="rejected", reason=reason)

    def _get(self, post_id):
        post = self.repo.get(post_id)
        if post is None:
            raise LookupError("post not found")
        return post

    def _pending(self, post_id):
        post = self._get(post_id)
        if post.status != "pending":
            raise ValueError(f"only pending posts can be reviewed (this post is {post.status})")
        return post
