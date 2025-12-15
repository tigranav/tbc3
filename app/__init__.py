from __future__ import annotations

from flask import Flask

from app.blueprints.test import test_blueprint
from app.blueprints.importer import importer_blueprint
from app.config import Config
from app.extensions import configure_pgdb, create_celery_app


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__)

    app_config = config or Config()
    app.config.from_object(app_config)

    configure_pgdb(app)
    create_celery_app(app)
    app.register_blueprint(test_blueprint)
    app.register_blueprint(importer_blueprint)

    @app.route("/")
    def root() -> tuple[str, int]:
        return "Application is running", 200

    return app
