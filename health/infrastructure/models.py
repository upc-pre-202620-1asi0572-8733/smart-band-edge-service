"""Peewee ORM model for the Health bounded context.

Defines the ``health_records`` database table structure used to persist
:class:`~health.domain.entities.HealthRecord` domain entities.  This module
belongs to the infrastructure layer and must not be referenced directly from
the domain or application layers; access is mediated through the repository.
"""
from peewee import Model, AutoField, FloatField, CharField, DateTimeField

from shared.infrastructure.database import db


class HealthRecord(Model):
    """ORM mapping for the ``health_records`` table.

    Each row represents a single heart-rate reading submitted by a registered
    smart band device.

    Attributes:
        id (AutoField): Auto-incrementing integer primary key assigned by the
            database on insert.
        device_id (CharField): Foreign reference to the device that produced
            the reading.  Stored as a plain string (not a FK constraint) to
            keep the bounded contexts loosely coupled.
        bpm (FloatField): Heart-rate measurement in beats per minute.
        created_at (DateTimeField): UTC timestamp of when the reading was
            captured by the device.
    """

    id = AutoField()
    device_id = CharField()
    bpm = FloatField()
    created_at = DateTimeField()

    class Meta:
        """Peewee metadata: binds the model to the shared database and names the table."""

        database = db
        table_name = 'health_records'

