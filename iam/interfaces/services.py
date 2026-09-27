"""Interface (REST API) layer for the IAM bounded context.

Exposes a Flask Blueprint (``iam_api``) and a shared authentication helper
(``authenticate_request``) used by other bounded contexts to guard their own
endpoints.  This layer owns no domain or business logic; it is concerned
solely with HTTP request/response handling and delegating to the application
service.
"""
from flask import Blueprint, request, jsonify
from pydantic import BaseModel, Field

from iam.application.services import AuthApplicationService

iam_api = Blueprint("iam_api", __name__)


class AuthRequest(BaseModel):
    """Pydantic model for validating the authentication request data."""

    device_id: str | None = Field(None, description="Identifier of the device.")


# Module-level singleton — instantiated once per worker process.
auth_service = AuthApplicationService()


def authenticate_request():
    """Validate the device identity for an incoming HTTP request.

    Extracts ``device_id`` from the JSON request body and ``X-API-Key`` from
    the request headers, then delegates to the IAM application service to
    verify the credentials against the device registry.

    This helper is intended to be called at the start of any route handler
    in a bounded context that requires device authentication::

        auth_result = authenticate_request()
        if auth_result:
            return auth_result  # short-circuit with 401

    **Expected request contract:**

    - ``Content-Type: application/json`` with a body containing ``device_id``.
    - ``X-API-Key`` header carrying the device's secret API key.

    Returns:
        tuple[flask.Response, int] | None: A ``(JSON response, 401)`` tuple
        when authentication fails (missing credentials or invalid pair);
        ``None`` when the request is successfully authenticated, allowing the
        caller to proceed with its own logic.
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "Missing X-API-Key"}), 401

    try:
        # We use a partial model or safe check since request.json might be missing
        if not request.json:
            return jsonify({"error": "Missing request body"}), 401

        auth_data = AuthRequest.model_validate(request.json)
        device_id = auth_data.device_id
    except Exception:
        return jsonify({"error": "Invalid request body"}), 401

    if not device_id:
        return jsonify({"error": "Missing device_id"}), 401

    if not auth_service.authenticate(device_id, api_key):
        return jsonify({"error": "Invalid device_id or API key"}), 401
    return None

