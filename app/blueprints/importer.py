from __future__ import annotations

from typing import Any, Dict, List

from celery import states
from flask import Blueprint, Response, current_app, jsonify, request, url_for

importer_blueprint = Blueprint("importer", __name__, url_prefix="/api/importer")


def _validate_records(raw_records: Any) -> List[Dict[str, Any]]:
    if raw_records is None:
        raise ValueError("`records` field is required")
    if not isinstance(raw_records, list) or not raw_records:
        raise ValueError("`records` must be a non-empty list")

    validated_records: List[Dict[str, Any]] = []
    for index, record in enumerate(raw_records):
        if not isinstance(record, dict):
            raise ValueError(f"Record at index {index} must be an object")

        try:
            record_id = record["id"]
            payload = record["payload"]
        except KeyError as exc:  # noqa: B904
            missing_key = exc.args[0]
            raise ValueError(f"Record at index {index} is missing required field '{missing_key}'") from exc

        if not isinstance(payload, str):
            raise ValueError(f"Record at index {index} has invalid payload type: expected string")

        validated_records.append({"id": str(record_id), "payload": payload})

    return validated_records


def _process_record(record: Dict[str, Any]) -> Dict[str, Any]:
    payload_text = record["payload"].strip()
    normalized_payload = payload_text.lower()

    return {
        "id": record["id"],
        "normalized_payload": normalized_payload,
        "original_length": len(record["payload"]),
        "trimmed_length": len(payload_text),
    }


@importer_blueprint.route("/ingest", methods=["POST"])
def ingest_records() -> tuple[Response, int]:
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400

    source = payload.get("source", "unspecified")
    if not isinstance(source, str):
        return jsonify({"status": "error", "message": "`source` must be a string"}), 400

    enqueue_tasks = bool(payload.get("enqueue"))

    try:
        records = _validate_records(payload.get("records"))
    except ValueError as exc:
        current_app.logger.warning("Importer validation failed: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 400

    if enqueue_tasks:
        try:
            from app.extensions import get_celery_app

            celery_app = get_celery_app(current_app)
            process_task = celery_app.tasks["app.tasks.importer.process_record_task"]
        except Exception as exc:  # noqa: BLE001
            current_app.logger.error("Celery dispatch failed: %s", exc)
            return jsonify({"status": "error", "message": "Celery is not configured"}), 503

        tasks = []
        for record in records:
            async_result = process_task.apply_async(args=[record], queue=celery_app.conf.task_default_queue)
            task_payload = {"record_id": record["id"], "task_id": async_result.id}
            if async_result.ready():
                task_payload["result"] = async_result.result
            tasks.append(task_payload)

        return (
            jsonify(
                {
                    "status": "queued",
                    "source": source,
                    "queued_tasks": len(tasks),
                    "tasks": tasks,
                }
            ),
            202,
        )

    processed_records = [_process_record(record) for record in records]

    return (
        jsonify(
            {
                "status": "ok",
                "source": source,
                "imported": len(processed_records),
                "results": processed_records,
            }
        ),
        200,
    )


@importer_blueprint.route("/progress", methods=["POST"])
def enqueue_progress_import() -> tuple[Response, int]:
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400

    try:
        records = _validate_records(payload.get("records"))
    except ValueError as exc:
        current_app.logger.warning("Progress task validation failed: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 400

    try:
        from app.extensions import get_celery_app

        celery_app = get_celery_app(current_app)
        process_task = celery_app.tasks["app.tasks.importer.process_batch_with_progress"]
    except Exception as exc:  # noqa: BLE001
        current_app.logger.error("Celery dispatch failed: %s", exc)
        return jsonify({"status": "error", "message": "Celery is not configured"}), 503

    async_result = process_task.apply_async(args=[records], queue=celery_app.conf.task_default_queue)
    status_path = url_for("importer.task_status", task_id=async_result.id)

    response_payload = {
        "status": "queued",
        "task_id": async_result.id,
        "status_url": status_path,
        "queue": celery_app.conf.task_default_queue,
    }

    if async_result.ready():
        response_payload["result"] = async_result.result

    return jsonify(response_payload), 202


@importer_blueprint.route("/status/<task_id>", methods=["GET"])
def task_status(task_id: str) -> tuple[Response, int]:
    try:
        from app.extensions import get_celery_app

        celery_app = get_celery_app(current_app)
    except Exception as exc:  # noqa: BLE001
        current_app.logger.error("Celery lookup failed: %s", exc)
        return jsonify({"status": "error", "message": "Celery is not configured"}), 503

    async_result = celery_app.AsyncResult(task_id)
    response_payload: Dict[str, Any] = {"task_id": task_id, "state": async_result.state}

    if async_result.info:
        if isinstance(async_result.info, dict):
            response_payload["meta"] = async_result.info
        else:
            response_payload["meta"] = {"details": str(async_result.info)}

    if async_result.successful():
        response_payload["result"] = async_result.result
        return jsonify(response_payload), 200

    if async_result.state == states.FAILURE:
        response_payload["error"] = str(async_result.result)

    return jsonify(response_payload), 200




@importer_blueprint.route("/import", methods=["POST"])
def import_file() -> tuple[Response, int]:
    payload = request.get_json(silent=True)
    #from libs.tbc_class import TBC
    pgdb = current_app.extensions["pgdb_factory"]
    #from libs.pgdb_class import pgdb
    #pg = pgdb()
    #res = pg.fetchone_dict("select count(*) from books")    
    with pgdb() as pg:
        res = pg.fetchone_dict("select * from books where id=345345")    

    return ( jsonify(res), 200)
