"""Domain entities for the IAM bounded context.

This module defines the aggregate root for the IAM bounded context.
Entities carry identity across their lifetime and encapsulate state that
is only modified by domain services enforcing business invariants.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Device:
    """Aggregate root representing a registered smart band device.

    A ``Device`` is the core identity object in the IAM bounded context.
    It is identified by a unique ``device_id`` and authenticated via its
    paired ``api_key``.  Device registration (creation) and look-up are
    managed by the :class:`~iam.infrastructure.repositories.DeviceRepository`.

    Attributes:
        device_id (str): Immutable, unique identifier for the device
            (e.g. ``'smart-band-001'``).
        api_key (str): Secret key used to authenticate HTTP requests
            originating from this device.  Transmitted via the
            ``X-API-Key`` header.
        created_at (datetime): UTC timestamp recording when the device was
            first registered in the system.
    """

    device_id: str
    api_key: str
    created_at: datetime

