import pytest

from app.db import connect


@pytest.fixture
def conn():
    """A fresh in-memory SQLite database for each test."""
    connection = connect(":memory:")
    yield connection
    connection.close()
