from __future__ import annotations

import pytest
from sqlalchemy.engine import Engine

from app import create_app
from app.config import Config
from app.db import Base
from app.extensions import get_engine


class GroupsConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"


@pytest.fixture()
def client():
    app = create_app(GroupsConfig())
    engine: Engine = get_engine(app)
    if engine.url.get_backend_name().startswith("sqlite"):
        with engine.begin() as connection:
            connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS tbc")
    Base.metadata.create_all(engine)
    with app.test_client() as client:
        yield client


def test_create_and_get_group(client):
    payload = {"id": 1, "name": "GPU", "comment": "CUDA queue"}
    create_response = client.post("/api/groups/", json=payload)
    assert create_response.status_code == 201
    created = create_response.get_json()
    assert created["status"] == "created"
    assert created["group"] == payload

    fetch_response = client.get("/api/groups/1")
    assert fetch_response.status_code == 200
    assert fetch_response.get_json() == payload


def test_list_update_and_delete_group(client):
    client.post("/api/groups/", json={"id": 2, "name": "CPU", "comment": "default"})
    client.post("/api/groups/", json={"id": 3, "name": "GPU", "comment": "accelerated"})

    list_response = client.get("/api/groups/")
    assert list_response.status_code == 200
    data = list_response.get_json()
    assert data["total"] == 2

    update_response = client.put("/api/groups/2", json={"name": "CPU", "comment": "general"})
    assert update_response.status_code == 200
    updated = update_response.get_json()["group"]
    assert updated["comment"] == "general"

    delete_response = client.delete("/api/groups/3")
    assert delete_response.status_code == 200
    delete_payload = delete_response.get_json()
    assert delete_payload["status"] == "deleted"

    missing_response = client.get("/api/groups/3")
    assert missing_response.status_code == 404


def test_duplicate_id_error(client):
    payload = {"id": 4, "name": "Archive", "comment": None}
    first = client.post("/api/groups/", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/api/groups/", json=payload)
    assert duplicate.status_code == 400
    assert duplicate.get_json()["status"] == "error"
