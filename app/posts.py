"""Posts module. Uses the Factory pattern: one place knows how to build an article or a vlog."""
import sqlite3
from dataclasses import dataclass

MIN_ARTICLE_CHARS = 20


@dataclass
class Post:
    id: int | None
    kind: str
    title: str
    body: str | None
    video_url: str | None
    author_id: int
    status: str = "draft"
    reason: str | None = None


def _build_article(author_id, title, body, video_url):
    body = (body or "").strip()
    if len(body) < MIN_ARTICLE_CHARS:
        raise ValueError(f"an article needs at least {MIN_ARTICLE_CHARS} characters of text")
    return Post(None, "article", title, body, None, author_id)


def _build_vlog(author_id, title, body, video_url):
    video_url = (video_url or "").strip()
    if not video_url.startswith(("http://", "https://")):
        raise ValueError("a vlog needs a video link starting with http:// or https://")
    return Post(None, "vlog", title, None, video_url, author_id)


# To add a new kind of post (for example "podcast"), write a builder and register it here.
BUILDERS = {"article": _build_article, "vlog": _build_vlog}


class PostFactory:
    @staticmethod
    def create(kind, author_id, title, body=None, video_url=None):
        if not title or not title.strip():
            raise ValueError("title is required")
        builder = BUILDERS.get(kind)
        if builder is None:
            raise ValueError(f"unknown post kind: {kind}")
        return builder(author_id, title.strip(), body, video_url)


class PostRepository:
    def __init__(self, conn):
        self.conn = conn

    def add(self, post):
        try:
            cursor = self.conn.execute(
                "INSERT INTO posts (kind, title, body, video_url, author_id, status) VALUES (?, ?, ?, ?, ?, ?)",
                (post.kind, post.title, post.body, post.video_url, post.author_id, post.status),
            )
        except sqlite3.IntegrityError:
            raise ValueError("unknown author") from None
        self.conn.commit()
        return cursor.lastrowid

    def get(self, post_id):
        row = self.conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        return Post(**dict(row)) if row else None

    def list(self, status=None):
        if status:
            rows = self.conn.execute("SELECT * FROM posts WHERE status = ? ORDER BY id", (status,))
        else:
            rows = self.conn.execute("SELECT * FROM posts ORDER BY id")
        return [Post(**dict(row)) for row in rows.fetchall()]

    def set_status(self, post_id, status, reason=None):
        self.conn.execute("UPDATE posts SET status = ?, reason = ? WHERE id = ?", (status, reason, post_id))
        self.conn.commit()

    def published_count(self, author_id):
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM posts WHERE author_id = ? AND status = 'published'", (author_id,)
        ).fetchone()
        return row["n"]


class PostService:
    def __init__(self, repo):
        self.repo = repo

    def create_draft(self, kind, author_id, title, body=None, video_url=None):
        post = PostFactory.create(kind, author_id, title, body, video_url)
        post.id = self.repo.add(post)
        return post

    def get(self, post_id):
        post = self.repo.get(post_id)
        if post is None:
            raise LookupError("post not found")
        return post

    def list(self, status=None):
        return self.repo.list(status)
