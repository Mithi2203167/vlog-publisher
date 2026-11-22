"""Subscriptions module: readers subscribe by email to be told about new posts."""
import sqlite3


class SubscriberRepository:
    def __init__(self, conn):
        self.conn = conn

    def add(self, email):
        try:
            self.conn.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        except sqlite3.IntegrityError:
            raise ValueError("already subscribed") from None
        self.conn.commit()

    def remove(self, email):
        cursor = self.conn.execute("DELETE FROM subscribers WHERE email = ?", (email,))
        self.conn.commit()
        return cursor.rowcount > 0

    def all_emails(self):
        return [row["email"] for row in self.conn.execute("SELECT email FROM subscribers ORDER BY id")]


class SubscriptionService:
    def __init__(self, repo):
        self.repo = repo

    def subscribe(self, email):
        email = (email or "").strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("invalid email address")
        self.repo.add(email)
        return email

    def unsubscribe(self, email):
        email = (email or "").strip().lower()
        if not self.repo.remove(email):
            raise LookupError("this email is not subscribed")

    def list(self):
        return self.repo.all_emails()
