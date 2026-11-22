import pytest

from app.authors import AuthorRepository, AuthorService
from app.comments import CommentRepository, CommentService
from app.posts import PostRepository, PostService

LONG_BODY = "Version control keeps a history of every change."


@pytest.fixture
def setup(conn):
    author = AuthorService(AuthorRepository(conn)).register("Rafi", "rafi@x.com")
    posts = PostRepository(conn)
    post = PostService(posts).create_draft("article", author.id, "Why Git?", body=LONG_BODY)
    return CommentService(CommentRepository(conn), posts), posts, post


def test_comment_on_published_post(setup):
    service, posts, post = setup
    posts.set_status(post.id, "published")
    comment = service.add(post.id, "Nusrat", "Nice post")
    assert comment["id"] is not None
    assert comment["text"] == "Nice post"


def test_comment_on_unpublished_post_is_rejected(setup):
    service, _, post = setup
    with pytest.raises(ValueError):
        service.add(post.id, "Nusrat", "Nice post")


def test_comment_on_missing_post_raises_lookup_error(setup):
    service, _, _ = setup
    with pytest.raises(LookupError):
        service.add(999, "Nusrat", "Nice post")


@pytest.mark.parametrize("name,text", [("", "Hello"), ("Nusrat", "  ")])
def test_comment_needs_name_and_text(setup, name, text):
    service, posts, post = setup
    posts.set_status(post.id, "published")
    with pytest.raises(ValueError):
        service.add(post.id, name, text)


def test_comments_are_listed_oldest_first(setup):
    service, posts, post = setup
    posts.set_status(post.id, "published")
    service.add(post.id, "A", "first")
    service.add(post.id, "B", "second")
    assert [c["text"] for c in service.list(post.id)] == ["first", "second"]
