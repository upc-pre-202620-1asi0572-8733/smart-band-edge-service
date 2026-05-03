"""Domain services for the Health bounded context.

Domain services encapsulate business logic that does not naturally belong to
a single entity.  ``HealthRecordService`` is responsible for validating raw
sensor input and constructing a well-formed :class:`~health.domain.entities.HealthRecord`
aggregate, enforcing the invariants of the Health bounded context.
"""
from datetime import datetime, timezone

from dateutil.parser import parse

from health.domain.entities import HealthRecord


class HealthRecordService:
    """Domain service responsible for the creation of valid health records.

    This service enforces the business invariants of the Health bounded
    context:

    - BPM must be a numeric value in the physiologically plausible range
      [0, 200].
    - ``created_at``, when supplied, must be a valid ISO 8601 timestamp;
      if omitted, the current UTC time is used.
    """

    @staticmethod
    def create_record(device_id: str, bpm: float, created_at: str | None) -> HealthRecord:
        """Validate raw sensor data and create a new :class:`HealthRecord` entity.

        Applies the domain invariants before constructing the aggregate:

        * ``bpm`` is coerced to ``float`` and validated in the range [0, 200].
        * ``created_at`` is parsed and converted to UTC; when ``None`` the
          current UTC timestamp is used.

        Args:
            device_id (str): Identifier of the originating device.
            bpm (float): Heart-rate reading in beats per minute.
            created_at (str | None): ISO 8601 timestamp of the reading
                (e.g. ``'2025-06-04T18:23:00-05:00'``), or ``None`` to
                default to the current UTC time.

        Returns:
            HealthRecord: A new, unsaved :class:`HealthRecord` domain entity
            with a UTC-normalized ``created_at`` value.

        Raises:
            ValueError: If ``bpm`` is not convertible to ``float``, falls
                outside [0, 200], or if ``created_at`` is not a valid ISO 8601
                string.
        """
        try:
            bpm = float(bpm)
            if not (0 <= bpm <= 200):
                raise ValueError("Invalid BPM value")
            if created_at:
                parsed_created_at = parse(created_at).astimezone(timezone.utc)
            else:
                parsed_created_at = datetime.now(timezone.utc)
        except (ValueError, TypeError):
            raise ValueError("Invalid data format")

        return HealthRecord(device_id, bpm, parsed_created_at)
