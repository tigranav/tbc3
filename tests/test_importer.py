from __future__ import annotations

import pytest

from app import create_app
from app.config import CeleryConfig, Config


class TestConfig(Config):
    TESTING = True


class EagerCeleryConfig(Config):
    TESTING = True
    CELERY_CONFIG = CeleryConfig(
        broker_url="redis://localhost:6379/0",
        result_backend="cache+memory://",
        default_queue="importer",
        task_always_eager=True,
        task_eager_propagates=True,
        task_store_eager_result=True,
    )


@pytest.fixture()
def client():
    app = create_app(TestConfig())
    with app.test_client() as client:
        yield client


@pytest.fixture()
def eager_client():
    app = create_app(EagerCeleryConfig())
    with app.test_client() as client:
        yield client


def test_ingest_records_success(client):
    payload = {
        "source": "unit-test",
        "records": [
            {"id": 1, "payload": "  Hello "},
            {"id": "b", "payload": "World"},
        ],
    }

    response = client.post("/api/importer/ingest", json=payload)

    assert response.status_code == 200
    data = response.get_json()
    assert data == {
        "status": "ok",
        "source": "unit-test",
        "imported": 2,
        "results": [
            {
                "id": "1",
                "normalized_payload": "hello",
                "original_length": 8,
                "trimmed_length": 5,
            },
            {
                "id": "b",
                "normalized_payload": "world",
                "original_length": 5,
                "trimmed_length": 5,
            },
        ],
    }


def test_ingest_records_validation_error(client):
    payload = {"source": "unit-test", "records": [{"id": 1}]}

    response = client.post("/api/importer/ingest", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "missing required field" in data["message"]


def test_ingest_records_enqueued(eager_client):
    payload = {
        "source": "unit-test",
        "enqueue": True,
        "records": [
            {"id": 3, "payload": "   queued"},
        ],
    }

    response = eager_client.post("/api/importer/ingest", json=payload)

    assert response.status_code == 202
    data = response.get_json()
    assert data["status"] == "queued"
    assert data["queued_tasks"] == 1
    task_info = data["tasks"][0]
    assert task_info["record_id"] == "3"
    assert task_info["result"]["normalized_payload"] == "queued"


def test_progress_task_status(eager_client):
    payload = {
        "records": [
            {"id": 1, "payload": "  GPU job  "},
            {"id": 2, "payload": " CPU job"},
        ]
    }

    enqueue_response = eager_client.post("/api/importer/progress", json=payload)

    assert enqueue_response.status_code == 202
    enqueue_data = enqueue_response.get_json()
    assert enqueue_data["status"] == "queued"
    task_id = enqueue_data["task_id"]

    status_response = eager_client.get(f"/api/importer/status/{task_id}")

    assert status_response.status_code == 200
    status_data = status_response.get_json()
    assert status_data["state"] == "SUCCESS"
    assert status_data["result"]["total"] == 2
    processed = status_data["result"]["processed"]
    assert processed[0]["normalized_payload"] == "gpu job"
    assert processed[1]["normalized_payload"] == "cpu job"
