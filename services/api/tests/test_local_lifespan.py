"""Lifecycle/configuration boundaries independent of running services."""

import asyncio
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from shipsense_api.local_readiness import LocalReadiness
from shipsense_api.main import create_app
from shipsense_local.stack import initialize


class LocalConfigurationTests(unittest.TestCase):
    def test_network_paths_are_rejected_before_loader_filesystem_or_clients(self):
        values = [
            prefix + "review.invalid" + separator + "share"
            for prefix in ("//", "\\\\", "/\\", "\\/")
            for separator in ("/", "\\")
        ] + [r"\\?\UNC\review.invalid\share", r"\\?\C:\state", r"\\.\C:\state"]
        for value in values:
            with (
                self.subTest(value=value),
                patch.dict(
                    os.environ,
                    {"SHIPSENSE_DEPENDENCIES": "test-fixtures", "SHIPSENSE_LOCAL_STATE_DIR": value},
                ),
                patch("shipsense_api.local_readiness.load_settings") as loader,
                patch("shipsense_api.local_readiness.LocalClients") as clients,
                patch.object(
                    Path, "stat", side_effect=AssertionError("filesystem reached")
                ) as stat,
                patch.object(
                    Path, "is_symlink", side_effect=AssertionError("filesystem reached")
                ) as symlink,
                patch.object(
                    Path, "open", side_effect=AssertionError("filesystem reached")
                ) as opened,
                self.assertLogs("shipsense.diagnostics") as logs,
                TestClient(create_app()) as client,
            ):
                response = client.get("/health/ready")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(client.get("/health/live").status_code, 200)
                self.assertEqual(client.get("/api/v1/version").status_code, 200)
                self.assertIsNone(client.app.state.local_runtime)
                self.assertNotIn("review.invalid", response.text + str(logs.output))
            loader.assert_not_called()
            clients.assert_not_called()
            stat.assert_not_called()
            symlink.assert_not_called()
            opened.assert_not_called()

    def test_shutdown_failure_does_not_expose_dependency_exception(self):
        runtime = AsyncMock()
        runtime.close.side_effect = RuntimeError("private-shutdown-value")
        with (
            patch.dict(
                os.environ,
                {
                    "SHIPSENSE_DEPENDENCIES": "test-fixtures",
                    "SHIPSENSE_LOCAL_STATE_DIR": "/external/state",
                },
            ),
            patch("shipsense_api.main.LocalReadiness.open", return_value=runtime),
            self.assertLogs("shipsense.diagnostics") as logs,
        ):
            app = create_app()
            with TestClient(app) as client:
                self.assertEqual(client.get("/health/live").status_code, 200)
        self.assertIsNone(app.state.local_runtime)
        self.assertNotIn("private-shutdown-value", str(logs.output))
        self.assertIn("dependency_adapters=shutdown_failed", str(logs.output))

    def test_invalid_configuration_is_read_only_redacted_and_never_installs_clients(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state"
            settings = initialize(state)
            original = {path.name: path.read_bytes() for path in state.iterdir()}
            variants = (
                ("local.json", b'{"unexpected":"private-invalid-value"}'),
                ("s3.json", b"{}"),
                ("local.json", json.dumps({"profile": "production"}).encode()),
                (
                    "local.json",
                    json.dumps(
                        json.loads(original["local.json"]) | {"repository": "/foreign/private"}
                    ).encode(),
                ),
            )
            for filename, invalid in variants:
                with self.subTest(filename=filename, invalid=invalid[:8]):
                    (state / filename).write_bytes(invalid)
                    before = {path.name: path.read_bytes() for path in state.iterdir()}
                    with (
                        patch.dict(
                            os.environ,
                            {
                                "SHIPSENSE_DEPENDENCIES": "test-fixtures",
                                "SHIPSENSE_LOCAL_STATE_DIR": str(state),
                            },
                        ),
                        patch("shipsense_api.local_readiness.LocalClients") as clients,
                        self.assertLogs("shipsense.diagnostics") as logs,
                        TestClient(create_app()) as client,
                    ):
                        response = client.get("/health/ready")
                        self.assertEqual(response.status_code, 503)
                        self.assertEqual(client.get("/health/live").status_code, 200)
                        self.assertEqual(client.get("/api/v1/version").status_code, 200)
                        self.assertIsNone(client.app.state.local_runtime)
                    clients.assert_not_called()
                    for value in (
                        str(state),
                        "private-invalid-value",
                        "/foreign/private",
                        settings.secret_key.get_secret_value(),
                    ):
                        self.assertNotIn(value, response.text + str(logs.output))
                    self.assertEqual(
                        before, {path.name: path.read_bytes() for path in state.iterdir()}
                    )
                    (state / filename).write_bytes(original[filename])

    def test_missing_empty_relative_and_network_config_do_not_create_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "never-created"
            for value in (str(missing), "", "relative-state", "//foreign/share"):
                with (
                    self.subTest(value=value),
                    patch.dict(
                        os.environ,
                        {
                            "SHIPSENSE_DEPENDENCIES": "test-fixtures",
                            "SHIPSENSE_LOCAL_STATE_DIR": value,
                        },
                    ),
                    TestClient(create_app()) as client,
                ):
                    self.assertEqual(client.get("/health/ready").status_code, 503)
                    self.assertEqual(client.get("/health/live").status_code, 200)
            self.assertFalse(missing.exists())


class ShutdownTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_shutdown_drains_workers_closes_clients_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state"
            initialize(state)
            runtime = await LocalReadiness.open(str(state))
            baseline = {thread.ident for thread in threading.enumerate()}
            started = threading.Event()
            release = threading.Event()

            def pending_work():
                started.set()
                release.wait(2)

            work = asyncio.create_task(runtime.clients.objects.call(pending_work))
            await asyncio.to_thread(started.wait, 1)
            close = asyncio.create_task(runtime.close())
            await asyncio.sleep(0.02)
            close.cancel()
            await asyncio.sleep(0.02)
            self.assertFalse(close.done())
            self.assertFalse(await runtime.queue_probe())
            self.assertFalse(await runtime.gate.ready())
            release.set()
            await work
            with self.assertRaises(asyncio.CancelledError):
                await close
            await runtime.close()
            self.assertFalse(runtime.clients.objects._pending)
            self.assertFalse(
                [
                    thread
                    for thread in threading.enumerate()
                    if thread.name.startswith("local-s3") and thread.ident not in baseline
                ]
            )
