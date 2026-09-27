"""Repository abstraction for Health domain aggregates."""

from typing import Protocol

from health.domain.entities import HealthRecord


class HealthRecordRepository(Protocol):
    """Persistence contract for Health records."""

    def save(self, health_record: HealthRecord) -> HealthRecord:
        """Persist a valid Health record and return its identified form."""
        ...
