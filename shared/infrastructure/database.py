"""Shared database infrastructure for the Smart Band Edge Service.

Provides a single :class:`peewee.SqliteDatabase` instance (``db``) that is
imported by ORM models across all bounded contexts, ensuring every model
operates on the same physical database file.

The :func:`init_db` helper is called once at application start-up to open a
connection and create any missing tables without affecting existing data
(``safe=True``).

Note:
    The ``db`` object itself is not connected until :func:`init_db` is
    called.  Peewee's ``SqliteDatabase`` manages the connection lifecycle
    via its own thread-local storage.
"""
from peewee import SqliteDatabase

# Shared SQLite database instance used by all bounded-context ORM models.
db = SqliteDatabase('smart_band.db')


def init_db() -> None:
    """Open the database connection and create all required tables.

    Imports the ORM models from the IAM and Health bounded contexts at call
    time (deferred import) to avoid circular dependencies during module
    loading, then issues a ``CREATE TABLE IF NOT EXISTS`` for each model.

    This function is idempotent: calling it when the tables already exist is
    safe and has no side-effects (``safe=True`` suppresses ``CREATE TABLE``
    errors for pre-existing tables).

    Side effects:
        - Opens a connection to ``smart_band.db`` (creating the file if it
          does not exist).
        - Creates the ``devices`` table if absent.
        - Creates the ``health_records`` table if absent.
        - Closes the connection after table creation.
    """
    db.connect()
    from iam.infrastructure.models import Device
    from health.infrastructure.models import HealthRecord
    db.create_tables([Device, HealthRecord], safe=True)
    db.close()

