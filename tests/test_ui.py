from __future__ import annotations

import pytest

from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"


@pytest.fixture()
def client():
    app = create_app(TestConfig())
    with app.test_client() as client:
        yield client


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Панель управления" in response.get_data(as_text=True)


def test_groups_page(client):
    response = client.get("/groups")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Группы файлов книг" in body
    assert "/api/groups" in body
