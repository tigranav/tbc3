from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class PostgresConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = ""
    database: str = "postgres"

    @classmethod
    def from_environ(cls) -> "PostgresConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", cls.host),
            port=int(os.getenv("POSTGRES_PORT", cls.port)),
            user=os.getenv("POSTGRES_USER", cls.user),
            password=os.getenv("POSTGRES_PASSWORD", cls.password),
            database=os.getenv("POSTGRES_DB", cls.database),
        )


@dataclass
class CeleryConfig:
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str | None = None
    default_queue: str = "default"
    task_acks_late: bool = True
    task_time_limit: int = 300
    task_always_eager: bool = False
    task_eager_propagates: bool = True
    task_store_eager_result: bool = False

    @staticmethod
    def _validated_broker_url(raw_url: str) -> str:
        if not raw_url.startswith(("redis://", "rediss://")):
            raise ValueError("CELERY_BROKER_URL must point to a Redis broker (redis:// or rediss://)")
        return raw_url

    @classmethod
    def from_environ(cls) -> "CeleryConfig":
        broker_url = cls._validated_broker_url(os.getenv("CELERY_BROKER_URL", cls.broker_url))
        return cls(
            broker_url=broker_url,
            result_backend=os.getenv("CELERY_RESULT_BACKEND", cls.result_backend),
            default_queue=os.getenv("CELERY_DEFAULT_QUEUE", cls.default_queue),
            task_acks_late=bool(int(os.getenv("CELERY_TASK_ACKS_LATE", str(int(cls.task_acks_late))))),
            task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", cls.task_time_limit)),
            task_always_eager=bool(int(os.getenv("CELERY_TASK_ALWAYS_EAGER", str(int(cls.task_always_eager))))),
            task_eager_propagates=bool(
                int(os.getenv("CELERY_TASK_EAGER_PROPAGATES", str(int(cls.task_eager_propagates))))
            ),
            task_store_eager_result=bool(
                int(os.getenv("CELERY_TASK_STORE_EAGER_RESULT", str(int(cls.task_store_eager_result))))
            ),
        )


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev")
    TESTING = False
    POSTGRES_CONFIG = PostgresConfig.from_environ()
    CELERY_CONFIG = CeleryConfig.from_environ()
