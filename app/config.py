from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class PostgresConfig:
    host: str = "192.168.0.50"
    port: int = 5433
    user: str = "tbc"
    password: str = "tbcpass"
    database: str = "books"

    @classmethod
    def from_environ(cls) -> "PostgresConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", cls.host),
            port=int(os.getenv("POSTGRES_PORT", cls.port)),
            user=os.getenv("POSTGRES_USER", cls.user),
            password=os.getenv("POSTGRES_PASSWORD", cls.password),
            database=os.getenv("POSTGRES_DB", cls.database),
        )


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev")
    TESTING = False
    POSTGRES_CONFIG = PostgresConfig.from_environ()
