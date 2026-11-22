"""Flask JSON API. create_app() wires services, the review policy and the observer together."""
import os
from dataclasses import asdict

from flask import Flask, jsonify, request

from app.authors import AuthorRepository, AuthorService
from app.comments import CommentRepository, CommentService
from app.db import connect
from app.notifier import ConsoleNotifier
from app.observers import EmailNotificationObserver, EventBus, format_post
from app.posts import PostRepository, PostService
from app.review import ManualReview, ReviewService
from app.subscriptions import SubscriberRepository, SubscriptionService


def create_app(config=None):
    config = config or {}
    app = Flask(__name__)

    conn = connect(config.get("DATABASE", os.environ.get("DATABASE_PATH", "publisher.db")))
    notifier = config.get("NOTIFIER") or ConsoleNotifier()
    policy = config.get("REVIEW_POLICY") or ManualReview()

    post_repo = PostRepository(conn)
    subscriber_repo = SubscriberRepository(conn)

    bus = EventBus()
    bus.subscribe("post.published", EmailNotificationObserver(notifier, subscriber_repo, format_post))

    authors = AuthorService(AuthorRepository(conn))
    posts = PostService(post_repo)
    review = ReviewService(post_repo, policy, bus)
    comments = CommentService(CommentRepository(conn), post_repo)
    subscriptions = SubscriptionService(subscriber_repo)

    @app.errorhandler(ValueError)
    def bad_request(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(LookupError)
    def not_found(error):
        return jsonify(error=str(error)), 404

    def body():
        return request.get_json(silent=True) or {}

    # ---- Web page (static HTML that calls the API below) ----
    @app.get("/")
    def home():
        return app.send_static_file("index.html")

    @app.get("/register")
    def register_page():
        return app.send_static_file("register.html")

    # ---- Authors ----
    @app.post("/authors")
    def register_author():
        data = body()
        return jsonify(asdict(authors.register(data.get("name"), data.get("email")))), 201

    @app.get("/authors")
    def list_authors():
        return jsonify([asdict(a) for a in authors.list()])

    # ---- Posts ----
    @app.post("/posts")
    def create_post():
        data = body()
        post = posts.create_draft(
            data.get("kind"), data.get("author_id"), data.get("title"), data.get("body"), data.get("video_url")
        )
        return jsonify(asdict(post)), 201

    @app.get("/posts")
    def list_posts():
        return jsonify([asdict(p) for p in posts.list(request.args.get("status"))])

    @app.get("/posts/<int:post_id>")
    def get_post(post_id):
        return jsonify(asdict(posts.get(post_id)))

    # ---- Review ----
    @app.post("/posts/<int:post_id>/submit")
    def submit_post(post_id):
        return jsonify(asdict(review.submit(post_id)))

    @app.post("/posts/<int:post_id>/approve")
    def approve_post(post_id):
        return jsonify(asdict(review.approve(post_id)))

    @app.post("/posts/<int:post_id>/reject")
    def reject_post(post_id):
        return jsonify(asdict(review.reject(post_id, body().get("reason"))))

    # ---- Comments ----
    @app.post("/posts/<int:post_id>/comments")
    def add_comment(post_id):
        data = body()
        return jsonify(comments.add(post_id, data.get("name"), data.get("text"))), 201

    @app.get("/posts/<int:post_id>/comments")
    def list_comments(post_id):
        return jsonify(comments.list(post_id))

    # ---- Subscriptions ----
    @app.post("/subscriptions")
    def subscribe():
        return jsonify(email=subscriptions.subscribe(body().get("email"))), 201

    @app.delete("/subscriptions")
    def unsubscribe():
        subscriptions.unsubscribe(body().get("email"))
        return jsonify(ok=True)

    @app.get("/subscriptions")
    def list_subscriptions():
        return jsonify(subscriptions.list())

    return app
