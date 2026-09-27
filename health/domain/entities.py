"""Domain entities for the Health bounded context.

This module defines the core aggregate of the Health bounded context.
Entities carry identity and encapsulate domain state; they should only be
created or mutated through domain services that enforce business invariants.
"""
from dataclasses import dataclass
from datetime import datetime

from health.domain.value_objects import HeartRateBpm, RecordedAt

@dataclass(frozen=True)
class SubmittingDevice:
    """Health's local representation of a device allowed to submit records."""

    device_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise ValueError("Device identifier cannot be empty")


@dataclass(frozen=True)
class HealthRecord:
    """A valid immutable health observation created through domain behavior.

    A ``HealthRecord`` captures a heart-rate measurement taken by a specific
    smart band device at a given point in time.

    Attributes:
        submitting_device (SubmittingDevice): Health's local device concept.
        heart_rate (HeartRateBpm): Validated heart-rate measurement.
        recorded_at (RecordedAt): Time of the observation, normalized to UTC.
        id (int | None): Surrogate identity assigned by the persistence layer
            after the record is saved.  ``None`` for transient (unsaved)
            instances.
    """

    submitting_device: SubmittingDevice
    heart_rate: HeartRateBpm
    recorded_at: RecordedAt
    id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.submitting_device, SubmittingDevice):
            raise TypeError("HealthRecord requires a SubmittingDevice")
        if not isinstance(self.heart_rate, HeartRateBpm):
            raise TypeError("HealthRecord requires a HeartRateBpm value")
        if not isinstance(self.recorded_at, RecordedAt):
            raise TypeError("HealthRecord requires a RecordedAt value")
        if self.id is not None:
            if isinstance(self.id, bool) or not isinstance(self.id, int) or self.id <= 0:
                raise ValueError("Persisted health record ID must be a positive integer")

    @classmethod
    def record(
        cls,
        submitting_device: SubmittingDevice,
        bpm: float,
        created_at: datetime | None,
    ) -> "HealthRecord":
        """Create a valid health record, enforcing domain invariants."""
        return cls(
            submitting_device,
            HeartRateBpm(bpm),
            RecordedAt.from_optional(created_at),
        )

    @property
    def device_id(self) -> str:
        """Return the submitting device's identifier."""
        return self.submitting_device.device_id

    @property
    def bpm(self) -> float:
        """Return the heart-rate measurement in beats per minute."""
        return self.heart_rate.value

    @property
    def created_at(self) -> datetime:
        """Return the UTC observation time."""
        return self.recorded_at.value

    def with_persistence_id(self, record_id: int) -> "HealthRecord":
        """Return this immutable record with its persistence identity."""
        return HealthRecord(
            self.submitting_device,
            self.heart_rate,
            self.recorded_at,
            record_id,
        )
