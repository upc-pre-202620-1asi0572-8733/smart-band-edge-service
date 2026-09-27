"""Application services for the Health bounded-context.

Application services sit between the interface layer and the domain layer.
They orchestrate use-cases by coordinating domain services, domain entities,
and repositories without containing domain logic themselves.
"""

from datetime import datetime

from health.application.errors import DeviceAuthenticationFailed
from health.domain.entities import HealthRecord, SubmittingDevice
from health.domain.repositories import HealthRecordRepository
from health.infrastructure.repositories import HealthRecordRepository as HealthRecordRepositoryImpl
from health.integration.iam_anti_corruption_layer import IamAntiCorruptionLayer


class HealthRecordApplicationService:
    """Application service that orchestrates the *create health record* use-case.

    Responsibilities:

    1. Cross-context validation – delegates IAM translation to the Health
       :class:`~health.integration.iam_anti_corruption_layer.IamAntiCorruptionLayer`.
    2. Domain logic – creates a valid :class:`~health.domain.entities.HealthRecord`
       through its domain factory.
    3. Persistence – delegates to: class:`~health.infrastructure.repositories.HealthRecordRepository` to
       persist the entity and return the saved aggregate with its assigned
       identity.
    """

    def __init__(
        self,
        iam_anti_corruption_layer: IamAntiCorruptionLayer,
        health_record_repository: HealthRecordRepository | None = None,
    ):
        """Initialize the service with its required collaborators."""
        self.health_record_repository = health_record_repository or HealthRecordRepositoryImpl()
        self.iam_anti_corruption_layer = iam_anti_corruption_layer

    def create_health_record(
        self, device_id: str, bpm: float, created_at: datetime | None, api_key: str
    ) -> HealthRecord:
        """Execute the *create health record* use-case.

        Validates that the device identified by ``device_id`` is registered
        and that the supplied ``api_key`` matches the stored credential before
        delegating record creation to the domain service and persisting the
        result.

        Args:
            device_id (str): Identifier of the device submitting the reading.
            bpm (float): Heart-rate measurement in beats per minute.
            created_at (datetime | None): Parsed timestamp of the reading. The
                domain record normalizes it to UTC and accepts ``None``
                to default to the current UTC time.
            api_key (str): The value of the ``X-API-Key`` request header used
                to authenticate the device.

        Returns:
            HealthRecord: The persisted: class:`~health.domain.entities.HealthRecord`
            entity populated with its assigned ``id``.

        Raises:
            DeviceAuthenticationFailed: If the credentials are not accepted.
            ValueError: If the domain rejects the sensor values.
        """
        submitting_device = self.iam_anti_corruption_layer.authenticated_submitting_device(
            device_id, api_key
        )
        if submitting_device is None:
            raise DeviceAuthenticationFailed
        record = HealthRecord.record(
            SubmittingDevice(submitting_device.device_id), bpm, created_at
        )
        return self.health_record_repository.save(record)
