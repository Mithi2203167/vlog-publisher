from unittest.mock import Mock

import pytest

from app.authors import AuthorRepository, AuthorService
from app.posts import PostFactory, PostRepository, PostService

LONG_BODY = "Version control keeps a history of every change."


# ---- Factory pattern -------------------------------------------------------
def test_factory_builds_article():
    post = PostFactory.create("article", 1, "Why Git?", body=LONG_BODY)
    assert post.kind == "article"
    assert post.body == LONG_BODY
    assert post.video_url is None
def test_service_get_returns_existing_post():
    repo = Mock()
    repo.get.return_value = "post"
    assert PostService(repo).get(1) == "post"

def test_factory_article_needs_enough_text():
    with pytest.raises(ValueError):
        PostFactory.create("article", 1, "Why Git?", body="short")


def test_factory_builds_vlog():
    post = PostFactory.create("vlog", 1, "Orientation day", video_url="https://youtu.be/abc")
    assert post.kind == "vlog"
    assert post.video_url == "https://youtu.be/abc"
    assert post.body is None


@pytest.mark.parametrize("url", [None, "", "not a url", "ftp://example.com/video"])
def test_factory_vlog_needs_http_url(url):
    with pytest.raises(ValueError):
        PostFactory.create("vlog", 1, "Orientation day", video_url=url)


def test_factory_rejects_unknown_kind():
    with pytest.raises(ValueError):
        PostFactory.create("podcast", 1, "Title", body=LONG_BODY)


def test_factory_requires_title():
    with pytest.raises(ValueError):
        PostFactory.create("article", 1, "  ", body=LONG_BODY)


def test_new_post_starts_as_draft():
    assert PostFactory.create("article", 1, "Why Git?", body=LONG_BODY).status == "draft"


# ---- Service (repository mocked) ------------------------------------------
def test_service_saves_draft_and_sets_id():
    repo = Mock()
    repo.add.return_value = 5
    post = PostService(repo).create_draft("article", 1, "Why Git?", body=LONG_BODY)
    assert post.id == 5
    repo.add.assert_called_once_with(post)


def test_service_does_not_save_invalid_post():
    repo = Mock()
    with pytest.raises(ValueError):
        PostService(repo).create_draft("vlog", 1, "No link")
    repo.add.assert_not_called()


def test_service_get_missing_post_raises():
    repo = Mock()
    repo.get.return_value = None
    with pytest.raises(LookupError):
        PostService(repo).get(9)


def test_service_list_passes_status_filter():
    repo = Mock()
    repo.list.return_value = ["x"]
    assert PostService(repo).list("published") == ["x"]
    repo.list.assert_called_once_with("published")


# ---- Repository (real in-memory SQLite) ------------------------------------
def make_author(conn):
    return AuthorService(AuthorRepository(conn)).register("Rafi", "rafi@x.com")


def test_repository_round_trip(conn):
    author = make_author(conn)
    repo = PostRepository(conn)
    post = PostService(repo).create_draft("article", author.id, "Why Git?", body=LONG_BODY)
    assert repo.get(post.id) == post


def test_repository_rejects_unknown_author(conn):
    with pytest.raises(ValueError):
        PostService(PostRepository(conn)).create_draft("article", 999, "Title", body=LONG_BODY)


def test_repository_filters_by_status_and_counts_published(conn):
    author = make_author(conn)
    repo = PostRepository(conn)
    service = PostService(repo)
    first = service.create_draft("article", author.id, "One", body=LONG_BODY)
    service.create_draft("article", author.id, "Two", body=LONG_BODY)
    repo.set_status(first.id, "published")
    assert [p.title for p in repo.list("published")] == ["One"]
    assert len(repo.list()) == 2
    assert repo.published_count(author.id) == 1
