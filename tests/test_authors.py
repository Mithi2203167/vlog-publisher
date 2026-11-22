import pytest

from app.authors import AuthorRepository, AuthorService


def make_service(conn):
    return AuthorService(AuthorRepository(conn))


def test_register_author_normalizes_email(conn):
    author = make_service(conn).register("  Rafi ", "Rafi@RUET.ac.bd")
    assert author.id is not None
    assert author.name == "Rafi"
    assert author.email == "rafi@ruet.ac.bd"


@pytest.mark.parametrize("name,email", [("", "a@x.com"), ("Rafi", "nope"), ("Rafi", "a@x")])
def test_register_rejects_invalid_input(conn, name, email):
    with pytest.raises(ValueError):
        make_service(conn).register(name, email)


def test_register_rejects_duplicate_email(conn):
    service = make_service(conn)
    service.register("Rafi", "rafi@x.com")
    with pytest.raises(ValueError):
        service.register("Another", "rafi@x.com")


def test_list_returns_registered_authors(conn):
    service = make_service(conn)
    service.register("A", "a@x.com")
    service.register("B", "b@x.com")
    assert [a.name for a in service.list()] == ["A", "B"]
