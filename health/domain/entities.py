"""Domain entities for the Health bounded context.

This module defines the core aggregate of the Health bounded context.
Entities carry identity and encapsulate domain state; they should only be
created or mutated through domain services that enforce business invariants.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HealthRecord:
    """Aggregate root representing a single health-monitoring reading.

    A ``HealthRecord`` captures a heart-rate measurement taken by a specific
    smart band device at a given point in time.  Instances are created by:
    meth:`~health.domain.services.HealthRecordService.create_record`, which
    validates the raw sensor data before constructing this entity.

    Attributes:
        device_id (str): Identifier of the device that produced the reading.
        bpm (float): Heart-rate measurement in beats per minute.
        created_at (datetime): UTC timestamp of when the reading was taken.
        id (int | None): Surrogate identity assigned by the persistence layer
            after the record is saved.  ``None`` for transient (unsaved)
            instances.
    """

    device_id: str
    bpm: float
    created_at: datetime
    id: int | None = None

