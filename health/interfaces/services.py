"""Interface (REST API) layer for the Health bounded context.

Exposes a Flask Blueprint (``health_api``) that translates incoming HTTP
requests into calls to the application service and maps the results back to
JSON responses.  This layer owns no domain logic; it is responsible solely
for I/O concerns: parsing request data, authentication delegation, and HTTP
status code selection.
"""
from flask import Blueprint, request, jsonify

from health.application.services import HealthRecordApplicationService
from iam.interfaces.services import authenticate_request

health_api = Blueprint("health_api", __name__)

# Module-level singleton; safe because Flask handles one request at a time
# within a single worker (no shared mutable state on this object).
health_record_service = HealthRecordApplicationService()


@health_api.route("/api/v1/health-monitoring/data-records", methods=["POST"])
def create_health_record():
    """Create a new health-monitoring data record.

    Validates the device identity via the ``X-API-Key`` header and the
    ``device_id`` field in the request body before delegating to the
    application service to apply domain rules and persist the record.

    **Request headers:**

    - ``X-API-Key`` *(required)*: API key paired with the device.
    - ``Content-Type: application/json`` *(required)*.

    **Request body (JSON):**

    .. code-block:: json

        {
            "device_id": "smart-band-001",
            "bpm": 72.5,
            "created_at": "2025-06-04T18:23:00-05:00"
        }

    - ``device_id`` *(str, required)*: Identifier of the submitting device.
    - ``bpm`` *(float, required)*: Heart-rate reading in beats per minute.
    - ``created_at`` *(str, optional)*: ISO 8601 timestamp; defaults to the
      current UTC time when omitted.

    **Responses:**

    - ``201 Created`` – Record saved successfully.  Body contains the
      persisted record with its assigned ``id`` and a UTC ``created_at``.
    - ``400 Bad Request`` – A required field is missing or a value is
      invalid (e.g. BPM out of range, malformed timestamp).
    - ``401 Unauthorized`` – ``device_id`` or ``X-API-Key`` is absent or
      does not match a registered device.

    Returns:
        tuple[flask.Response, int]: A JSON response body paired with the
        appropriate HTTP status code.
    """
    auth_result = authenticate_request()
    if auth_result:
        return auth_result

    data = request.json
    try:
        device_id = data["device_id"]
        bpm = data["bpm"]
        created_at = data.get("created_at")
        record = health_record_service.create_health_record(
            device_id, bpm, created_at, request.headers.get("X-API-Key")
        )
        return jsonify({
            "id": record.id,
            "device_id": record.device_id,
            "bpm": record.bpm,
            "created_at": record.created_at.isoformat() + "Z"
        }), 201
    except KeyError:
        return jsonify({"error": "Missing required fields"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

