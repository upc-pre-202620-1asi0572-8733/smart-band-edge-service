"""Application services for the Health bounded-context.

Application services sit between the interface layer and the domain layer.
They orchestrate use-cases by coordinating domain services, domain entities,
and repositories without containing domain logic themselves.
"""

from health.domain.entities import HealthRecord
from health.domain.services import HealthRecordService, HealthRecordRepository
from health.infrastructure.repositories import HealthRecordRepository as HealthRecordRepositoryImpl
from iam.domain.services import DeviceRepository
from iam.infrastructure.repositories import DeviceRepository as DeviceRepositoryImpl


class HealthRecordApplicationService:
    """Application service that orchestrates the *create health record* use-case.

    Responsibilities:

    1. Cross-context validation – delegates to the `IAM` bounded-context.
       :class:`~iam.infrastructure.repositories.DeviceRepository` to verify
       that the requesting device is registered and the supplied API key is
       valid.
    2. Domain logic – delegates to: class:`~health.domain.services.HealthRecordService` to validate
        the raw sensor values and construct a: class:`~health.domain.entities.HealthRecord`
       entity.
    3. Persistence – delegates to: class:`~health.infrastructure.repositories.HealthRecordRepository` to
       persist the entity and return the saved aggregate with its assigned
       identity.
    """

    def __init__(
        self,
        health_record_repository: HealthRecordRepository | None = None,
        health_record_service: HealthRecordService | None = None,
        device_repository: DeviceRepository | None = None,
    ):
        """Initialize the service with its required collaborators."""
        self.health_record_repository = health_record_repository or HealthRecordRepositoryImpl()
        self.health_record_service = health_record_service or HealthRecordService()
        self.device_repository = device_repository or DeviceRepositoryImpl()

    def create_health_record(self, device_id: str, bpm: float, created_at: str, api_key: str) -> HealthRecord:
        """Execute the *create health record* use-case.

        Validates that the device identified by ``device_id`` is registered
        and that the supplied ``api_key`` matches the stored credential before
        delegating record creation to the domain service and persisting the
        result.

        Args:
            device_id (str): Identifier of the device submitting the reading.
            bpm (float): Heart-rate measurement in beats per minute.
            created_at (str): ISO 8601 timestamp of the reading.  Passed
                directly to the domain service, which also accepts ``None``
                to default to the current UTC time.
            api_key (str): The value of the ``X-API-Key`` request header used
                to authenticate the device.

        Returns:
            HealthRecord: The persisted: class:`~health.domain.entities.HealthRecord`
            entity populated with its assigned ``id``.

        Raises:
            ValueError: If no device matches the given ``device_id`` /
                ``api_key`` combination, or if the domain service rejects the
                sensor values (invalid BPM or malformed timestamp).
        """
        # Cross-context guard: verify device identity via the IAM repository.
        if not self.device_repository.find_by_id_and_api_key(device_id, api_key):
            raise ValueError("Device not found")
        record = self.health_record_service.create_record(device_id, bpm, created_at)
        return self.health_record_repository.save(record)

