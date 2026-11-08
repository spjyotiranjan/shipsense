import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from shipsense_api.main import create_app

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("validate_foundation", ROOT / "scripts/validate-foundation.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class FoundationTests(unittest.TestCase):
    def test_public_local_diagnostic_contains_no_customer_data(self):
        with patch.dict(os.environ, {"SHIPSENSE_PROFILE": "local"}):
            with TestClient(create_app()) as client:
                response = client.get("/foundation")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"service": "shipsense-api", "mode": "local-foundation"})
                self.assertEqual(client.get("/customers").status_code, 404)
                self.assertIn("/foundation", client.get("/openapi.json").json()["paths"])

    def test_unsupported_profile_does_not_echo_value(self):
        with patch.dict(os.environ, {"SHIPSENSE_PROFILE": "secret-example"}):
            with self.assertRaisesRegex(RuntimeError, "^SHIPSENSE_PROFILE must be local for the foundation.$"):
                create_app()

    def test_missing_fixture_and_config_fail_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            with self.assertRaisesRegex(ValueError, "^FIXTURE_MISSING$"):
                validator.validate(missing, ROOT / "infra/local.example.json")
            with self.assertRaisesRegex(ValueError, "^CONFIG_MISSING$"):
                validator.validate(ROOT / "tests/fixtures/foundation.json", missing)

    def test_untrusted_fixture_rejected(self):
        original = json.loads((ROOT / "tests/fixtures/foundation.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "fixture.json"
            for changed in ({"environment": "production"}, {"provider": "github"}, {"unexpected": "secret-example"}, {"eventTime": "invalid"}):
                with self.subTest(changed=changed):
                    fixture.write_text(json.dumps(original | changed))
                    with self.assertRaisesRegex(ValueError, "^INVALID_FIXTURE$"):
                        validator.validate(fixture, ROOT / "infra/local.example.json")
            fixture.write_bytes(b"x" * 8193)
            with self.assertRaisesRegex(ValueError, "^INPUT_TOO_LARGE$"):
                validator.validate(fixture, ROOT / "infra/local.example.json")

    def test_committed_inputs_validate(self):
        validator.validate(ROOT / "tests/fixtures/foundation.json", ROOT / "infra/local.example.json")
