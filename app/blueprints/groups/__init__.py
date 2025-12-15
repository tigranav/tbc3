from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from flask import Blueprint, Response, current_app, jsonify, request

from app.blueprints.groups.repository import BooksFilesGroupRepository
from app.extensions import get_session


groups_blueprint = Blueprint("groups", __name__, url_prefix="/api/groups")


@contextmanager
def _repository() -> Iterator[BooksFilesGroupRepository]:
    session = get_session(current_app)
    try:
        yield BooksFilesGroupRepository(session)
    finally:
        session.close()


def _parse_payload(require_id: bool = False) -> tuple[int | None, str | None, str | None]:
    payload = request.get_json(silent=True) or {}
    if require_id:
        if "id" not in payload:
            raise ValueError("Field 'id' is required")
        group_id = int(payload["id"])
    else:
        group_id = None
    name = payload.get("name")
    comment = payload.get("comment")
    return group_id, name, comment


@groups_blueprint.get("/")
def list_groups() -> Response:
    with _repository() as repo:
        groups = [group.to_dict() for group in repo.list_groups()]
    return jsonify({"items": groups, "total": len(groups)})


@groups_blueprint.get("/<int:group_id>")
def get_group(group_id: int) -> tuple[Response, int] | Response:
    with _repository() as repo:
        group = repo.get_group(group_id)
        if group is None:
            return jsonify({"status": "not_found", "message": "Group not found"}), 404
        return jsonify(group.to_dict())


@groups_blueprint.post("/")
def create_group() -> tuple[Response, int]:
    try:
        group_id, name, comment = _parse_payload(require_id=True)
    except (TypeError, ValueError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    with _repository() as repo:
        try:
            created = repo.create_group(group_id=group_id, name=name, comment=comment)
        except ValueError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400
    return jsonify({"status": "created", "group": created.to_dict()}), 201


@groups_blueprint.put("/<int:group_id>")
def update_group(group_id: int) -> tuple[Response, int] | Response:
    _, name, comment = _parse_payload()
    with _repository() as repo:
        updated = repo.update_group(group_id, name=name, comment=comment)
        if updated is None:
            return jsonify({"status": "not_found", "message": "Group not found"}), 404
        return jsonify({"status": "updated", "group": updated.to_dict()})


@groups_blueprint.delete("/<int:group_id>")
def delete_group(group_id: int) -> tuple[Response, int]:
    with _repository() as repo:
        deleted = repo.delete_group(group_id)
        if not deleted:
            return jsonify({"status": "not_found", "message": "Group not found"}), 404
    return jsonify({"status": "deleted", "id": group_id})
