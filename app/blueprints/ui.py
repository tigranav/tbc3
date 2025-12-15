from __future__ import annotations

from flask import Blueprint, render_template

ui_blueprint = Blueprint("ui", __name__)


@ui_blueprint.get("/")
def index() -> str:
    return render_template("index.html")


@ui_blueprint.get("/groups")
def groups_page() -> str:
    return render_template("groups.html")


@ui_blueprint.get("/types")
def types_page() -> str:
    return render_template("types.html")
