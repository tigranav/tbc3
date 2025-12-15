from __future__ import annotations

from celery import Celery

from app import create_app
from app.config import Config
from app.extensions import create_celery_app


def _create_celery() -> Celery:
    flask_app = create_app(Config())
    return create_celery_app(flask_app)


celery: Celery = _create_celery()

