import os
import tempfile
import unittest

_test_directory = tempfile.TemporaryDirectory(prefix="smart-band-test-")
os.environ["DATABASE_PATH"] = os.path.join(_test_directory.name, "test.db")
os.environ["SEED_TEST_DEVICE"] = "1"
os.environ["TEST_DEVICE_API_KEY"] = "test-only-key"

from app import create_app


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

    def test_rejects_non_json_requests_with_unsupported_media_type(self):
        response = self.client.post(
            "/api/v1/health-monitoring/data-records",
            data="{}",
            content_type="text/plain",
            headers={"X-API-Key": "test-only-key"},
        )

        self.assertEqual(response.status_code, 415)


if __name__ == "__main__":
    unittest.main()
