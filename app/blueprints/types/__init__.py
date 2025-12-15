from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from flask import Blueprint, Response, current_app, jsonify, request

from app.blueprints.types.repository import BooksFilesTypeRepository
from app.extensions import get_session


types_blueprint = Blueprint("types", __name__, url_prefix="/api/types")


@contextmanager
def _repository() -> Iterator[BooksFilesTypeRepository]:
    session = get_session(current_app)
    try:
        yield BooksFilesTypeRepository(session)
    finally:
        session.close()


def _parse_payload(require_id: bool = False) -> tuple[int | None, str | None, str | None, int | None]:
    payload = request.get_json(silent=True) or {}
    if require_id:
        if "id" not in payload:
            raise ValueError("Field 'id' is required")
        type_id = int(payload["id"])
    else:
        type_id = None
    file_name = payload.get("file_name")
    comments = payload.get("comments")
    group_id = payload.get("group_id")
    if group_id is not None:
        group_id = int(group_id)
    return type_id, file_name, comments, group_id


@types_blueprint.get("/")
def list_types() -> Response:
    with _repository() as repo:
        items = [item.to_dict() for item in repo.list_types()]
    return jsonify({"items": items, "total": len(items)})


@types_blueprint.get("/<int:type_id>")
def get_type(type_id: int) -> tuple[Response, int] | Response:
    with _repository() as repo:
        item = repo.get_type(type_id)
        if item is None:
            return jsonify({"status": "not_found", "message": "Type not found"}), 404
        return jsonify(item.to_dict())


@types_blueprint.post("/")
def create_type() -> tuple[Response, int]:
    try:
        type_id, file_name, comments, group_id = _parse_payload(require_id=True)
    except (TypeError, ValueError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    if group_id is None:
        return jsonify({"status": "error", "message": "group_id is required"}), 400

    with _repository() as repo:
        try:
            created = repo.create_type(
                type_id=type_id, file_name=file_name, comments=comments, group_id=group_id
            )
        except ValueError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400
    return jsonify({"status": "created", "type": created.to_dict()}), 201


@types_blueprint.put("/<int:type_id>")
def update_type(type_id: int) -> tuple[Response, int] | Response:
    try:
        _, file_name, comments, group_id = _parse_payload()
    except (TypeError, ValueError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    with _repository() as repo:
        try:
            updated = repo.update_type(
                type_id, file_name=file_name, comments=comments, group_id=group_id
            )
        except ValueError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

        if updated is None:
            return jsonify({"status": "not_found", "message": "Type not found"}), 404
        return jsonify({"status": "updated", "type": updated.to_dict()})


@types_blueprint.delete("/<int:type_id>")
def delete_type(type_id: int) -> tuple[Response, int]:
    with _repository() as repo:
        deleted = repo.delete_type(type_id)
        if not deleted:
            return jsonify({"status": "not_found", "message": "Type not found"}), 404
    return jsonify({"status": "deleted", "id": type_id})
