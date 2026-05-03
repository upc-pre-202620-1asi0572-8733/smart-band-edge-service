"""Domain entities for the Health bounded context.

This module defines the core aggregate of the Health bounded context.
Entities carry identity and encapsulate domain state; they should only be
created or mutated through domain services that enforce business invariants.
"""
from datetime import datetime


class HealthRecord:
    """Aggregate root representing a single health-monitoring reading.

    A ``HealthRecord`` captures a heart-rate measurement taken by a specific
    smart band device at a given point in time.  Instances are created by
    :meth:`~health.domain.services.HealthRecordService.create_record`, which
    validates the raw sensor data before constructing this entity.

    Attributes:
        id (int | None): Surrogate identity assigned by the persistence layer
            after the record is saved.  ``None`` for transient (unsaved)
            instances.
        device_id (str): Identifier of the device that produced the reading.
        bpm (float): Heart-rate measurement in beats per minute.
        created_at (datetime): UTC timestamp of when the reading was taken.
    """

    def __init__(self, device_id: str, bpm: float, created_at: datetime, id: int = None):
        """Initialise a HealthRecord entity.

        Args:
            device_id (str): Identifier of the originating device.
            bpm (float): Heart-rate in beats per minute.
            created_at (datetime): UTC timestamp of the reading.
            id (int, optional): Persistence identity.  Defaults to ``None``
                for transient entities that have not been saved yet.
        """
        self.id = id
        self.device_id = device_id
        self.bpm = bpm
        self.created_at = created_at

