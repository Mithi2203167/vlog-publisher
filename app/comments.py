"""Comments module: readers comment on published posts."""


class CommentRepository:
    def __init__(self, conn):
        self.conn = conn

    def add(self, post_id, name, text):
        cursor = self.conn.execute(
            "INSERT INTO comments (post_id, name, text) VALUES (?, ?, ?)", (post_id, name, text)
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM comments WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)

    def list_for_post(self, post_id):
        rows = self.conn.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY id", (post_id,))
        return [dict(row) for row in rows.fetchall()]


class CommentService:
    def __init__(self, repo, post_repo):
        self.repo = repo
        self.posts = post_repo

    def add(self, post_id, name, text):
        if not name or not name.strip() or not text or not text.strip():
            raise ValueError("name and text are required")
        post = self.posts.get(post_id)
        if post is None:
            raise LookupError("post not found")
        if post.status != "published":
            raise ValueError("comments are only allowed on published posts")
        return self.repo.add(post_id, name.strip(), text.strip())

    def list(self, post_id):
        return self.repo.list_for_post(post_id)
