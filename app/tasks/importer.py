from __future__ import annotations

from typing import Any, Dict, List

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

    @celery_app.task(bind=True, name="app.tasks.importer.process_batch_with_progress")
    def process_batch_with_progress(
        self, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process multiple records while reporting progress."""

        if not isinstance(records, list):
            raise TypeError("Records payload must be a list")

        processed_records: List[Dict[str, Any]] = []
        total = len(records)

        for index, record in enumerate(records):
            processed_records.append(_process_record(record))
            progress_percentage = int(((index + 1) / max(total, 1)) * 100)
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": index + 1,
                    "total": total,
                    "progress": progress_percentage,
                },
            )

        return {"processed": processed_records, "total": total}

    celery_app.tasks.register(process_batch_with_progress)
