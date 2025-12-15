from __future__ import annotations

from typing import Any

from celery import Celery
from flask import Flask

from app.config import CeleryConfig, PostgresConfig
from libs.pgdb_class import pgdb


def configure_pgdb(app: Flask) -> None:
    postgres_config: PostgresConfig | None = app.config.get("POSTGRES_CONFIG")
    if not isinstance(postgres_config, PostgresConfig):
        raise TypeError("POSTGRES_CONFIG must be a PostgresConfig instance")

    pgdb.PG_HOST = postgres_config.host
    pgdb.PG_PORT = postgres_config.port
    pgdb.PG_USER = postgres_config.user
    pgdb.PG_PASSWORD = postgres_config.password
    pgdb.PG_DB = postgres_config.database

    app.extensions["pgdb_factory"] = pgdb


def get_db_factory(app: Flask) -> type[pgdb]:
    factory: Any = app.extensions.get("pgdb_factory")
    if factory is None:
        raise LookupError("Database factory is not configured. Call configure_pgdb first.")
    if not isinstance(factory, type) or not issubclass(factory, pgdb):
        raise TypeError("Configured database factory is invalid")
    return factory


def create_celery_app(app: Flask) -> Celery:
    celery_config: CeleryConfig | None = app.config.get("CELERY_CONFIG")
    if not isinstance(celery_config, CeleryConfig):
        raise TypeError("CELERY_CONFIG must be a CeleryConfig instance")

    celery_app = Celery(
        app.import_name,
        broker=celery_config.broker_url,
        backend=celery_config.result_backend,
        include=["app.tasks.importer"],
        set_as_current=True,
    )
    celery_app.conf.update(
        task_default_queue=celery_config.default_queue,
        task_acks_late=celery_config.task_acks_late,
        task_time_limit=celery_config.task_time_limit,
        task_always_eager=celery_config.task_always_eager,
        task_eager_propagates=celery_config.task_eager_propagates,
        task_store_eager_result=celery_config.task_store_eager_result,
    )
    from app.tasks import importer as importer_tasks

    importer_tasks.register_importer_tasks(celery_app)

    TaskBase = celery_app.Task

    class ContextTask(TaskBase):  # type: ignore[misc]
        abstract = True

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery_app.Task = ContextTask  # type: ignore[assignment]
    app.extensions["celery_app"] = celery_app
    return celery_app


def get_celery_app(app: Flask) -> Celery:
    celery_app: Any = app.extensions.get("celery_app")
    if celery_app is None:
        raise LookupError("Celery is not configured. Call create_celery_app first.")
    if not isinstance(celery_app, Celery):
        raise TypeError("Configured Celery application is invalid")
    return celery_app
