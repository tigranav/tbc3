from __future__ import annotations

import pytest

from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True


@pytest.fixture()
def client():
    app = create_app(TestConfig())
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
