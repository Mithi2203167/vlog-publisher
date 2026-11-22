"""Authors module: people who write articles and post vlogs."""
import sqlite3
from dataclasses import dataclass


@dataclass
class Author:
    id: int
    name: str
    email: str


class AuthorRepository:
    def __init__(self, conn):
        self.conn = conn

    def add(self, name, email):
        try:
            cursor = self.conn.execute("INSERT INTO authors (name, email) VALUES (?, ?)", (name, email))
        except sqlite3.IntegrityError:
            raise ValueError("email is already registered") from None
        self.conn.commit()
        return Author(cursor.lastrowid, name, email)

    def list(self):
        rows = self.conn.execute("SELECT * FROM authors ORDER BY id").fetchall()
        return [Author(**dict(row)) for row in rows]


class AuthorService:
    def __init__(self, repo):
        self.repo = repo

    def register(self, name, email):
        name = (name or "").strip()
        email = (email or "").strip().lower()
        if not name:
            raise ValueError("name is required")
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("invalid email address")
        return self.repo.add(name, email)

    def list(self):
        return self.repo.list()
