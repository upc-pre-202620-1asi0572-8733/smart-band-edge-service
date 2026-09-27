"""Interface (REST API) layer for the Health bounded-context.

Exposes a Flask Blueprint (``health_api``) that translates incoming HTTP
requests into calls to the application service and maps the results back to
JSON responses.  This layer owns no domain logic; it is responsible solely
for I/O concerns: parsing request data, authentication delegation, and HTTP
status code selection.
"""
from flask import Blueprint, current_app, jsonify, request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from health.application.errors import DeviceAuthenticationFailed

health_api = Blueprint("health_api", __name__)


class HealthRecordCreateRequest(BaseModel):
    """Pydantic model for validating the create health record request body."""

    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(..., description="Identifier of the submitting device.")
    bpm: float = Field(..., ge=0, le=200, description="Heart-rate reading in beats per minute.")
    created_at: str | None = Field(None, description="ISO 8601 timestamp.")


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
    - ``400 Bad Request`` – A required field is missing, or a value is
      invalid (i.e., BPM out of range, malformed timestamp).
    - ``401 Unauthorized`` – ``device_id`` or ``X-API-Key`` is absent or
      does not match a registered device.

    Returns:
        tuple[flask.Response, int]: A JSON response body paired with the
        appropriate HTTP status code.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 415
        request_data = request.get_json(silent=True)
        if request_data is None:
            return jsonify({"error": "Invalid JSON request body"}), 400
        if isinstance(request_data, dict) and not request_data.get("device_id"):
            return jsonify({"error": "Missing device_id"}), 401
        req_data = HealthRecordCreateRequest.model_validate(request_data)
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"error": "Missing X-API-Key"}), 401
        record = current_app.extensions["health_record_service"].create_health_record(
            req_data.device_id, req_data.bpm, req_data.created_at, api_key
        )
        return jsonify({
            "id": record.id,
            "device_id": record.device_id,
            "bpm": record.bpm,
            "created_at": record.created_at.isoformat() + "Z"
        }), 201
    except ValidationError:
        return jsonify({"error": "Invalid health record request"}), 400
    except DeviceAuthenticationFailed:
        return jsonify({"error": "Invalid device_id or API key"}), 401
    except ValueError:
        return jsonify({"error": "Invalid health record data"}), 400
