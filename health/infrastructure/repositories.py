"""Repository implementation for the Health bounded context.

Provides the persistence adapter that maps between the
:class:`~health.domain.entities.HealthRecord` domain entity and the
:class:`~health.infrastructure.models.HealthRecord` Peewee ORM model.

Following the Repository pattern, callers in the application layer interact
only with domain entities and are shielded from ORM/database details.
"""
from health.domain.entities import HealthRecord
from health.infrastructure.models import HealthRecord as HealthRecordModel


class HealthRecordRepository:
    """Repository that persists and reconstructs :class:`~health.domain.entities.HealthRecord` entities.

    Acts as an in-process collection of domain entities backed by the SQLite
    database.  The mapping between the ORM model and the domain entity is
    handled entirely within this class, keeping the domain layer free of
    infrastructure concerns.
    """

    @staticmethod
    def save(health_record: HealthRecord) -> HealthRecord:
        """Persist a transient :class:`~health.domain.entities.HealthRecord` entity.

        Inserts a new row into the ``health_records`` table using Peewee's
        ``create`` helper and returns a new domain entity instance populated
        with the database-assigned ``id``.

        Args:
            health_record (HealthRecord): The transient entity to persist.
                Its ``id`` attribute is expected to be ``None`` at this point.

        Returns:
            HealthRecord: A new :class:`~health.domain.entities.HealthRecord`
            instance that is a copy of the input enriched with the
            auto-assigned ``id`` from the database.
        """
        record = HealthRecordModel.create(
            device_id=health_record.device_id,
            bpm=health_record.bpm,
            created_at=health_record.created_at,
        )
        return HealthRecord(
            health_record.device_id,
            health_record.bpm,
            health_record.created_at,
            record.id,
        )

