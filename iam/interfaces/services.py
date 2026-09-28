"""Interface (REST API) layer for the IAM bounded context.

Exposes IAM HTTP routes and adapts request data for the IAM application
service. ``authenticate_request`` is an HTTP helper for route handlers; other
bounded contexts use IAM's application use case through their own integration
components instead of depending on this interface.
"""
from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from iam.application.services import AuthApplicationService

iam_api = Blueprint("iam_api", __name__)


class AuthRequest(BaseModel):
    """Pydantic model for validating the authentication request data."""

    # Ignore additional payload fields outside IAM's authentication contract.
    model_config = ConfigDict(extra="ignore")

    device_id: str | None = Field(None, description="Identifier of the device.")


# Module-level singleton — instantiated once per worker process.
auth_service = AuthApplicationService()


def authenticate_request() -> tuple | None:
    """Authenticate the device described by the current HTTP request.

    Extracts ``device_id`` from the JSON request body and ``X-API-Key`` from
    the request headers, validates the HTTP payload, then delegates
    authentication to IAM's application service. This helper belongs to the
    HTTP interface and is not the contract for communication between
    bounded contexts.

    **Expected request contract:**

    - ``Content-Type: application/json`` with a body containing ``device_id``.
    - ``X-API-Key`` header carrying the device's secret API key.

    Returns:
        An HTTP error response and status code when the request is malformed
        or authentication fails; ``None`` when authentication succeeds.
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "Missing X-API-Key"}), 401

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    request_data = request.get_json(silent=True)
    if request_data is None:
        return jsonify({"error": "Invalid JSON request body"}), 400

    try:
        device_id = AuthRequest.model_validate(request_data).device_id
    except ValidationError:
        return jsonify({"error": "Invalid request body"}), 400

    if not device_id:
        return jsonify({"error": "Missing device_id"}), 401

    if not auth_service.authenticate(device_id, api_key):
        return jsonify({"error": "Invalid device_id or API key"}), 401
    return None
