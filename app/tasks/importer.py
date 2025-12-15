from __future__ import annotations

from typing import Any, Dict

from celery import Celery

from app.blueprints.importer import _process_record


def register_importer_tasks(celery_app: Celery) -> None:
    @celery_app.task(name="app.tasks.importer.process_record_task")
    def process_record_task(record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize an importer record asynchronously."""

        if not isinstance(record, dict):
            raise TypeError("Record payload must be a dictionary")

        return _process_record(record)

    celery_app.tasks.register(process_record_task)
