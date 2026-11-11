"""Real socket lifecycle and failure-preserving smoke cleanup regressions."""

import importlib.util
import json
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    "integration_smoke", Path(__file__).resolve().parents[1] / "integration-smoke.py"
)
assert spec is not None and spec.loader is not None
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class SmokeLifecycleTests(unittest.TestCase):
    def test_live_listener_is_refused_and_preserved(self) -> None:
        with socket.create_server(("127.0.0.1", 0)) as server:
            port = server.getsockname()[1]
            with self.assertRaisesRegex(smoke.LocalFailure, "SMOKE_PORT_CONFLICT"):
                smoke.assert_free(port)
            # The failed check must not disrupt the pre-existing listener.
            with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
                server.settimeout(2)
                connection, _ = server.accept()
                with connection:
                    connection.sendall(b"preserved")
                    self.assertEqual(client.recv(16), b"preserved")

    def test_server_closed_connection_can_rebind_immediately(self) -> None:
        with socket.create_server(("127.0.0.1", 0)) as server:
            port = server.getsockname()[1]
            with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
                server.settimeout(2)
                connection, _ = server.accept()
                with connection:
                    # The server actively closes, leaving its port in TIME_WAIT
                    # on Linux, as HTTP shutdown does in the real smoke.
                    connection.shutdown(socket.SHUT_WR)
                    self.assertEqual(client.recv(1), b"")
        if sys.platform.startswith("linux"):
            with socket.socket() as bare:
                with self.assertRaises(OSError):
                    bare.bind(("127.0.0.1", port))
        smoke.assert_free(port)
        with socket.create_server(("127.0.0.1", port)) as restarted:
            self.assertEqual(restarted.getsockname()[1], port)

    def test_initial_failure_and_cancellation_survive_cleanup_failure(self) -> None:
        for failure in (smoke.LocalFailure("SMOKE_STARTUP_FAILED"), KeyboardInterrupt()):
            with self.subTest(failure=type(failure).__name__), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                child = Mock()
                child.stop.side_effect = subprocess.TimeoutExpired("owned-test", 10)
                with (
                    patch.object(smoke, "assert_free"),
                    patch.object(smoke, "start_api", return_value=child),
                    patch.object(smoke, "wait_http", side_effect=failure),
                    self.assertRaises(type(failure)) as caught,
                ):
                    smoke.smoke(directory, hosted=False, fail_upstream=False)
                self.assertIs(caught.exception, failure)
                self.assertFalse(
                    json.loads((directory / "cleanup.json").read_text())["ownedProcessesStopped"]
                )
                self.assertFalse((directory / "smoke.json").exists())

    def test_cleanup_attempts_every_child_and_port_before_failing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first, last = Mock(), Mock()
            last.stop.side_effect = OSError("synthetic failure")
            with (
                patch.object(
                    smoke, "assert_free", side_effect=smoke.LocalFailure("SMOKE_PORT_CONFLICT")
                ) as probe,
                self.assertRaisesRegex(smoke.LocalFailure, "OWNED_PROCESS_CLEANUP_FAILED"),
            ):
                smoke.cleanup(Path(tmp), [first, last], None)
            first.stop.assert_called_once()
            last.stop.assert_called_once()
            self.assertEqual(probe.call_count, 2)
            self.assertEqual(
                json.loads((Path(tmp) / "cleanup.json").read_text()),
                {"ownedProcessesStopped": False, "portsAvailable": False},
            )

    def test_success_is_not_recorded_if_cleanup_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            with (
                patch.object(smoke, "assert_free"),
                patch.object(smoke, "start_api"),
                patch.object(smoke, "wait_http"),
                patch.object(smoke, "request"),
                patch.object(smoke.VersionResponse, "model_validate"),
                patch.object(smoke, "Child"),
                patch.object(
                    smoke, "cleanup", side_effect=smoke.LocalFailure("OWNED_PROCESS_CLEANUP_FAILED")
                ),
                self.assertRaisesRegex(smoke.LocalFailure, "OWNED_PROCESS_CLEANUP_FAILED"),
            ):
                smoke.smoke(directory, hosted=False, fail_upstream=False)
            self.assertFalse((directory / "smoke.json").exists())


if __name__ == "__main__":
    unittest.main()
