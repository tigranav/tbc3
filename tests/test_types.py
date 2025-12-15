from __future__ import annotations

import pytest
from sqlalchemy.engine import Engine

from app import create_app
from app.config import Config
from app.db import Base
from app.extensions import get_engine


class TypesConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"


@pytest.fixture()
def client():
    app = create_app(TypesConfig())
    engine: Engine = get_engine(app)
    if engine.url.get_backend_name().startswith("sqlite"):
        with engine.begin() as connection:
            connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS tbc")
    Base.metadata.create_all(engine)
    with app.test_client() as client:
        yield client


def _create_group(client, group_id: int) -> None:
    client.post("/api/groups/", json={"id": group_id, "name": f"G{group_id}", "comment": None})


def test_create_and_get_type(client):
    _create_group(client, 1)
    payload = {"id": 10, "file_name": "chapter.pdf", "comments": "PDF", "group_id": 1}
    response = client.post("/api/types/", json=payload)
    assert response.status_code == 201
    created = response.get_json()
    assert created["status"] == "created"
    assert created["type"]["group_id"] == 1

    fetch_response = client.get("/api/types/10")
    assert fetch_response.status_code == 200
    fetched = fetch_response.get_json()
    assert fetched["file_name"] == "chapter.pdf"
    assert fetched["group_id"] == 1


def test_list_update_and_delete_type(client):
    _create_group(client, 2)
    _create_group(client, 3)
    client.post("/api/types/", json={"id": 20, "file_name": "audio", "comments": None, "group_id": 2})
    client.post(
        "/api/types/",
        json={"id": 21, "file_name": "video", "comments": "4k", "group_id": 3},
    )

    list_response = client.get("/api/types/")
    assert list_response.status_code == 200
    assert list_response.get_json()["total"] == 2

    update_response = client.put(
        "/api/types/20",
        json={"file_name": "audio", "comments": "stereo", "group_id": 3},
    )
    assert update_response.status_code == 200
    updated = update_response.get_json()["type"]
    assert updated["comments"] == "stereo"
    assert updated["group_id"] == 3

    delete_response = client.delete("/api/types/21")
    assert delete_response.status_code == 200
    assert delete_response.get_json()["status"] == "deleted"

    missing_response = client.get("/api/types/21")
    assert missing_response.status_code == 404


def test_group_validation_errors(client):
    _create_group(client, 4)
    # Missing group
    response = client.post(
        "/api/types/",
        json={"id": 30, "file_name": "doc", "comments": None, "group_id": 999},
    )
    assert response.status_code == 400
    assert response.get_json()["status"] == "error"

    # Update with non-existing group
    client.post(
        "/api/types/",
        json={"id": 31, "file_name": "doc", "comments": "ok", "group_id": 4},
    )
    update_response = client.put("/api/types/31", json={"group_id": 1000})
    assert update_response.status_code == 400
    assert update_response.get_json()["status"] == "error"
