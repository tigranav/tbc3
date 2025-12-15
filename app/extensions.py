from __future__ import annotations

from typing import Any

from flask import Flask

from app.config import PostgresConfig
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
