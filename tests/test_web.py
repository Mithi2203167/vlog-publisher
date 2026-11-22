from unittest.mock import Mock

import pytest

from app.api import create_app


@pytest.fixture
def client():
    return create_app({"DATABASE": ":memory:", "NOTIFIER": Mock()}).test_client()


def test_home_page_is_served_with_the_main_controls(client):
    response = client.get("/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    for element_id in ("post-btn", "pending-list", "published-list", "who"):
        assert f'id="{element_id}"' in html


def test_home_page_links_to_the_registration_page(client):
    assert 'href="/register"' in client.get("/").get_data(as_text=True)


def test_registration_page_is_served_with_its_form(client):
    response = client.get("/register")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    for element_id in ("author-name", "author-email", "author-btn", "author-status"):
        assert f'id="{element_id}"' in html
