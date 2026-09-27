import os
import tempfile
import unittest
from datetime import UTC, datetime

_test_directory = tempfile.TemporaryDirectory(prefix="smart-band-test-")
os.environ["DATABASE_PATH"] = os.path.join(_test_directory.name, "test.db")
os.environ["SEED_TEST_DEVICE"] = "1"
os.environ["TEST_DEVICE_API_KEY"] = "test-only-key"

from app import create_app
from health.domain.entities import SubmittingDevice
from health.integration.iam_anti_corruption_layer import IamAntiCorruptionLayer
from iam.infrastructure.models import Device as DeviceModel


class IamAntiCorruptionLayerTestCase(unittest.TestCase):
    def test_translates_iam_authentication_to_health_concept(self):
        class FakeIamAuthenticationService:
            credentials = None

            def authenticate(self, device_id, api_key):
                self.credentials = (device_id, api_key)
                return True

        iam_service = FakeIamAuthenticationService()
        layer = IamAntiCorruptionLayer(iam_service)

        self.assertEqual(
            layer.authenticated_submitting_device("band-42", "secret"),
            SubmittingDevice("band-42"),
        )
        self.assertEqual(iam_service.credentials, ("band-42", "secret"))

    def test_returns_no_health_concept_when_iam_rejects_credentials(self):
        class RejectingIamAuthenticationService:
            def authenticate(self, device_id, api_key):
                return False

        layer = IamAntiCorruptionLayer(RejectingIamAuthenticationService())

        self.assertIsNone(layer.authenticated_submitting_device("band-42", "invalid"))


class HealthApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.testing = True

    def setUp(self):
        self.client = self.app.test_client()

    def test_creates_authenticated_record(self):
        response = self.client.post(
            "/api/v1/health-monitoring/data-records",
            json={
                "device_id": "smart-band-001",
                "bpm": 72,
                "created_at": "2026-09-27T15:00:00-05:00",
            },
            headers={"X-API-Key": "test-only-key"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["created_at"], "2026-09-27T20:00:00+00:00Z")

    def test_rejects_naive_timestamp(self):
        response = self.client.post(
            "/api/v1/health-monitoring/data-records",
            json={"device_id": "smart-band-001", "bpm": 72, "created_at": "2026-09-27T15:00:00"},
            headers={"X-API-Key": "test-only-key"},
        )

        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_device_credentials(self):
        response = self.client.post(
            "/api/v1/health-monitoring/data-records",
            json={"device_id": "smart-band-001", "bpm": 72},
            headers={"X-API-Key": "invalid-key"},
        )

        self.assertEqual(response.status_code, 401)

    def test_rejects_non_json_requests_with_unsupported_media_type(self):
        response = self.client.post(
            "/api/v1/health-monitoring/data-records",
            data="{}",
            content_type="text/plain",
            headers={"X-API-Key": "test-only-key"},
        )

        self.assertEqual(response.status_code, 415)

    def test_device_lifecycle_changes_are_persisted(self):
        iam_service = self.app.extensions["iam_authentication_service"]
        iam_service.register_device("lifecycle-device", "first-secret")
        with self.assertRaises(ValueError):
            iam_service.register_device("lifecycle-device", "duplicate-secret")

        self.assertTrue(iam_service.authenticate("lifecycle-device", "first-secret"))
        iam_service.rotate_api_key("lifecycle-device", "second-secret")
        self.assertFalse(iam_service.authenticate("lifecycle-device", "first-secret"))
        self.assertTrue(iam_service.authenticate("lifecycle-device", "second-secret"))
        iam_service.revoke_device("lifecycle-device")
        self.assertFalse(iam_service.authenticate("lifecycle-device", "second-secret"))

        stored = DeviceModel.get_by_id("lifecycle-device").credential_verifier
        self.assertNotEqual(stored, "second-secret")

    def test_migrates_legacy_plaintext_credentials(self):
        DeviceModel.create(
            device_id="legacy-device",
            credential_verifier="legacy-secret",
            created_at=datetime.now(UTC),
            revoked_at=None,
        )

        iam_service = self.app.extensions["iam_authentication_service"]
        DeviceModel._meta.database.execute_sql(
            'ALTER TABLE "devices" DROP COLUMN "revoked_at"'
        )
        iam_service.device_repository.migrate_schema()

        self.assertTrue(iam_service.authenticate("legacy-device", "legacy-secret"))
        columns = {
            column.name
            for column in DeviceModel._meta.database.get_columns("devices")
        }
        self.assertIn("revoked_at", columns)
        self.assertTrue(
            DeviceModel.get_by_id("legacy-device").credential_verifier.startswith(
                "pbkdf2_sha256$"
            )
        )


if __name__ == "__main__":
    unittest.main()
