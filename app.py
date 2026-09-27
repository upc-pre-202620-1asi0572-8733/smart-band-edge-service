"""Flask application entry point for the Smart Band Edge Service.

This module wires together the Flask application, registers the IAM and
Health bounded-context Blueprints, configures the SQLite database, and
composes the Health-to-IAM anti-corruption layer.

Typical usage::

    flask --app app run
    # or
    python app.py
"""

import os

from flask import Flask

from health.application.services import HealthRecordApplicationService
from health.integration.iam_anti_corruption_layer import IamAntiCorruptionLayer
from health.infrastructure.repositories import HealthRecordRepository
from health.interfaces.services import health_api
from iam.application.services import AuthApplicationService
from iam.interfaces.services import iam_api
from iam.infrastructure.repositories import DeviceRepository
from shared.infrastructure.database import configure_database, db, init_db


def create_app() -> Flask:
    """Create and initialize the Flask application."""
    app = Flask(__name__)
    configure_database(os.getenv("DATABASE_PATH", "smart_band.db"))
    init_db()
    DeviceRepository().migrate_schema()
    HealthRecordRepository().migrate_schema()
    app.config["SEED_TEST_DEVICE"] = os.getenv("SEED_TEST_DEVICE", "0") == "1"
    app.config["TEST_DEVICE_ID"] = os.getenv("TEST_DEVICE_ID", "smart-band-001")
    app.config["TEST_DEVICE_API_KEY"] = os.getenv("TEST_DEVICE_API_KEY")

    app.register_blueprint(iam_api)
    app.register_blueprint(health_api)
    iam_authentication_service = AuthApplicationService()
    app.extensions["iam_authentication_service"] = iam_authentication_service
    app.extensions["health_record_service"] = HealthRecordApplicationService(
        iam_anti_corruption_layer=IamAntiCorruptionLayer(iam_authentication_service)
    )

    if app.config["SEED_TEST_DEVICE"]:
        if not app.config["TEST_DEVICE_API_KEY"]:
            raise RuntimeError("TEST_DEVICE_API_KEY is required when SEED_TEST_DEVICE=1")
        iam_authentication_service.get_or_create_test_device(
            app.config["TEST_DEVICE_ID"],
            app.config["TEST_DEVICE_API_KEY"],
        )

    @app.teardown_appcontext
    def close_database(_exception: BaseException | None) -> None:
        if not db.is_closed():
            db.close()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
