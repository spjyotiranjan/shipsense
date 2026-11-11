"""Hosted lifespan errors remain generic without service provisioning."""

import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from shipsense_api.main import create_app


class LifespanTests(unittest.TestCase):
    def test_shutdown_failure_does_not_expose_provider_exception(self):
        runtime = AsyncMock()
        runtime.close.side_effect = RuntimeError("private-shutdown-value")
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("shipsense_api.main.HostedReadiness.from_environment", return_value=runtime),
            self.assertLogs("shipsense.diagnostics") as logs,
            TestClient(create_app()) as client,
        ):
            self.assertEqual(client.get("/health/live").status_code, 200)
        self.assertNotIn("private-shutdown-value", str(logs.output))
        runtime.close.assert_awaited_once()
