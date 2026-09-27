"""Environment-specific application configuration."""

import os
from pathlib import Path
from typing import TypedDict

from dotenv import dotenv_values


class AppConfig(TypedDict):
    APP_ENV: str
    DEBUG: bool
    DATABASE_PATH: str
    SEED_TEST_DEVICE: bool
    TEST_DEVICE_ID: str
    TEST_DEVICE_API_KEY: str | None
    HOST: str
    PORT: int


_DEFAULTS = {
    "DEBUG": "false",
    "SEED_TEST_DEVICE": "false",
    "TEST_DEVICE_ID": "smart-band-001",
    "TEST_DEVICE_API_KEY": "",
    "HOST": "127.0.0.1",
    "PORT": "5000",
}


def _as_bool(name: str, value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def load_config(project_root: Path) -> AppConfig:
    """Load defaults, selected dotenv values, then process environment overrides."""
    environment_name = os.getenv("APP_ENV", "development").strip().lower()
    if environment_name not in {"development", "production"}:
        raise ValueError("APP_ENV must be 'development' or 'production'")

    values = {
        **_DEFAULTS,
        "DATABASE_PATH": (
            "smart_band.db" if environment_name == "development" else "var/smart_band.db"
        ),
        **{
            key: value
            for key, value in dotenv_values(project_root / f".env.{environment_name}").items()
            if value is not None
        },
        **os.environ,
    }

    debug = _as_bool("DEBUG", values["DEBUG"])
    seed_test_device = _as_bool("SEED_TEST_DEVICE", values["SEED_TEST_DEVICE"])
    if environment_name == "production" and debug:
        raise ValueError("DEBUG must be false in production")
    if environment_name == "production" and seed_test_device:
        raise ValueError("SEED_TEST_DEVICE must be false in production")

    database_path = values["DATABASE_PATH"]
    if not database_path.strip():
        raise ValueError("DATABASE_PATH cannot be empty")
    database = Path(database_path).expanduser()
    if not database.is_absolute():
        database = project_root / database

    try:
        port = int(values["PORT"])
    except ValueError as error:
        raise ValueError("PORT must be an integer") from error
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")

    api_key = values["TEST_DEVICE_API_KEY"].strip() or None
    if seed_test_device and not api_key:
        raise ValueError("TEST_DEVICE_API_KEY is required when seeding is enabled")
    device_id = values["TEST_DEVICE_ID"].strip()
    host = values["HOST"].strip()
    if seed_test_device and not device_id:
        raise ValueError("TEST_DEVICE_ID cannot be empty when seeding is enabled")
    if not host:
        raise ValueError("HOST cannot be empty")

    return {
        "APP_ENV": environment_name,
        "DEBUG": debug,
        "DATABASE_PATH": str(database),
        "SEED_TEST_DEVICE": seed_test_device,
        "TEST_DEVICE_ID": device_id,
        "TEST_DEVICE_API_KEY": api_key,
        "HOST": host,
        "PORT": port,
    }
