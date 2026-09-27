"""Domain services for the IAM bounded context.

Domain services express business behavior that does not fit neatly inside a
single entity.  ``AuthService`` encapsulates the authentication invariant for
the IAM bounded context: a device is considered authenticated when it exists
in the repository (i.e. it was found by matching both ``device_id`` and
``api_key``).
"""
from typing import Protocol

from iam.domain.entities import Device


class DeviceRepository(Protocol):
    """Protocol for device persistence."""

    def find_by_id_and_api_key(self, device_id: str, api_key: str) -> Device | None:
        """Look up a device by its identifier and API key."""
        ...

    def get_or_create_test_device(self, device_id: str, api_key: str) -> Device:
        """Retrieve the default test device, creating it if absent."""
        ...


class AuthService:
    """Domain service that determines whether a device is authenticated.

    The authentication rule is deliberately kept simple: a ``Device`` object
    that was successfully retrieved from the repository is, by definition,
    authenticated.  Absent or unrecognized credentials result in ``None``
    being passed to this service, which returns ``False``.
    """

    @staticmethod
    def authenticate(device: Device | None) -> bool:
        """Determine whether the given device is authenticated.

        The :class:`~iam.infrastructure.repositories.DeviceRepository` returns
        ``None`` when no device matches the supplied credentials; a non-``None``
        value indicates that the ``device_id`` / ``api_key`` pair is valid.

        Args:
            device (Device | None): The device entity returned by the
                repository look-up, or ``None`` if no matching device was found.

        Returns:
            bool: ``True`` if ``device`` is not ``None`` (authentication
            succeeds); ``False`` otherwise.
        """
        return device is not None
