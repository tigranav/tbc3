from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify

from app.extensions import get_db_factory


test_blueprint = Blueprint("test", __name__, url_prefix="/api")


@test_blueprint.route("/health", methods=["GET"])
def healthcheck() -> Response:
    return jsonify({"status": "ok"})


@test_blueprint.route("/db-status", methods=["GET"])
def database_status() -> tuple[Response, int] | Response:
    try:
        db_factory = get_db_factory(current_app)
        with db_factory() as db:
            version_row = db.fetchone("select version()")
            version = version_row[0] if version_row else "unknown"
    except Exception as exc:  # noqa: BLE001
        current_app.logger.warning("Database connection failed: %s", exc)
        return jsonify({"status": "error", "message": "Database unavailable"}), 503

    return jsonify({"status": "ok", "postgres_version": version})
