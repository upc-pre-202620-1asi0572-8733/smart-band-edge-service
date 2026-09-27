import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config import load_config


class LoadConfigTestCase(unittest.TestCase):
    def test_loads_selected_dotenv_and_process_environment_overrides_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env.development").write_text(
                "DEBUG=true\nDATABASE_PATH=local.db\nPORT=4000\n"
            )
            with patch.dict(
                os.environ,
                {"APP_ENV": "development", "DATABASE_PATH": "override.db"},
                clear=True,
            ):
                config = load_config(root)

        self.assertTrue(config["DEBUG"])
        self.assertEqual(config["PORT"], 4000)
        self.assertEqual(config["DATABASE_PATH"], str(root / "override.db"))

    def test_production_defaults_are_secure(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"APP_ENV": "production"}, clear=True
        ):
            config = load_config(Path(directory))

        self.assertFalse(config["DEBUG"])
        self.assertFalse(config["SEED_TEST_DEVICE"])
        self.assertIsNone(config["TEST_DEVICE_API_KEY"])
        self.assertEqual(config["DATABASE_PATH"], str(Path(directory) / "var/smart_band.db"))

    def test_loading_another_environment_does_not_reuse_dotenv_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env.development").write_text("DEBUG=true\n")
            (root / ".env.production").write_text("DEBUG=false\n")
            with patch.dict(os.environ, {}, clear=True):
                development = load_config(root)
                os.environ["APP_ENV"] = "production"
                production = load_config(root)

        self.assertTrue(development["DEBUG"])
        self.assertFalse(production["DEBUG"])

    def test_rejects_debug_or_test_seeding_in_production(self):
        for setting in (
            {"DEBUG": "true"},
            {"SEED_TEST_DEVICE": "true", "TEST_DEVICE_API_KEY": "local-secret"},
        ):
            with self.subTest(setting=setting), tempfile.TemporaryDirectory() as directory:
                with patch.dict(
                    os.environ, {"APP_ENV": "production", **setting}, clear=True
                ), self.assertRaises(ValueError):
                    load_config(Path(directory))

    def test_requires_key_for_development_device_seed(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"APP_ENV": "development", "SEED_TEST_DEVICE": "true"},
            clear=True,
        ), self.assertRaisesRegex(ValueError, "TEST_DEVICE_API_KEY"):
            load_config(Path(directory))

    def test_rejects_invalid_environment_boolean_and_port(self):
        for environ in (
            {"APP_ENV": "staging"},
            {"APP_ENV": "development", "DEBUG": "sometimes"},
            {"APP_ENV": "development", "PORT": "70000"},
        ):
            with self.subTest(environ=environ), tempfile.TemporaryDirectory() as directory:
                with patch.dict(os.environ, environ, clear=True), self.assertRaises(ValueError):
                    load_config(Path(directory))


if __name__ == "__main__":
    unittest.main()
