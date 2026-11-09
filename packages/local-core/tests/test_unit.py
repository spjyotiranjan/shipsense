"""Local safety boundaries without a running dependency."""

import asyncio
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pydantic import ValidationError
from shipsense_local.adapters import PrivateObjects
from shipsense_local.cli import main
from shipsense_local.config import ROOT, LocalFailure, load_settings, state_path
from shipsense_local.fixtures import CASES, Manifest, load_fixture
from shipsense_local.queue import Envelope, MemoryQueue
from shipsense_local.stack import LocalStack, initialize


class ConfigurationTests(unittest.TestCase):
    def test_ci_namespace_is_opt_in_and_swapped_state_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            local = initialize(root / "local")
            ci = initialize(root / "ci", project="shipsense-ci-p01")
            self.assertEqual(local.project, "shipsense-local-p01")
            self.assertNotEqual(local.owner, ci.owner)
            self.assertNotEqual(local.secret_key, ci.secret_key)
            self.assertEqual(load_settings(root / "local"), local)
            with self.assertRaisesRegex(LocalFailure, "UNOWNED_LOCAL_TARGET"):
                initialize(root / "local", project="shipsense-ci-p01")
            with self.assertRaisesRegex(LocalFailure, "UNOWNED_LOCAL_TARGET"):
                LocalStack(root / "ci", ci)
            with self.assertRaisesRegex(LocalFailure, "LOCAL_CONFIG_MISMATCH"):
                LocalStack(root / "local", ci, project="shipsense-ci-p01")
            with patch.dict(os.environ, {"COMPOSE_PROJECT_NAME": "foreign"}):
                with self.assertRaisesRegex(LocalFailure, "INHERITED_NAMESPACE_REFUSED"):
                    LocalStack(root / "ci", ci, project="shipsense-ci-p01")
            settings = json.loads((root / "ci/local.json").read_text())
            settings["project"] = "arbitrary-project"
            (root / "ci/local.json").write_text(json.dumps(settings))
            with self.assertRaises(LocalFailure):
                load_settings(root / "ci")

    def test_ci_resource_requires_owner_namespace_and_state_labels(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "ci"
            ci = initialize(directory, project="shipsense-ci-p01")
            stack = LocalStack(directory, ci, project="shipsense-ci-p01")
            for changes in (
                {"shipsense.owner": "stale-owner"},
                {"shipsense.state": "swapped-state"},
                {"com.docker.compose.project": "shipsense-local-p01"},
            ):
                labels = {
                    "shipsense.owner": ci.owner,
                    "shipsense.state": stack.state_identity,
                    "com.docker.compose.project": "shipsense-ci-p01",
                    **changes,
                }
                with (
                    patch.object(stack, "local_engine", return_value={}),
                    patch.object(
                        stack,
                        "docker",
                        side_effect=[
                            "shipsense-ci-p01-mongodb-1\n",
                            json.dumps([{"Config": {"Labels": labels}}]),
                        ],
                    ),
                    patch.object(stack, "compose") as compose,
                ):
                    with self.assertRaisesRegex(LocalFailure, "UNOWNED_LOCAL_RESOURCE"):
                        stack.down(reset=True, confirmation="shipsense-ci-p01")
                    compose.assert_not_called()

    def test_partial_launch_failure_is_cleaned_up_by_cli_without_reset(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "state"
            stack = LocalStack(directory, initialize(directory))
            commands = []

            def compose(*arguments):
                commands.append(arguments)
                if arguments[0] == "up":
                    raise LocalFailure("DOCKER_COMMAND_FAILED")

            output = io.StringIO()
            with (
                patch("sys.argv", ["local", "up", "--state-dir", str(directory)]),
                patch("shipsense_local.cli.LocalStack", return_value=stack),
                patch.object(stack, "validate_ownership", return_value={}) as ownership,
                patch.object(stack, "preflight", return_value={}),
                patch.object(stack, "compose", side_effect=compose),
                patch("shipsense_local.cli.wait_for_services") as wait,
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(main(), 2)
            self.assertEqual(json.loads(output.getvalue()), {"error": "DOCKER_COMMAND_FAILED"})
            self.assertEqual(
                commands, [("up", "--detach", "--pull", "missing", "--no-build"), ("down",)]
            )
            self.assertEqual(ownership.call_count, 2)
            wait.assert_not_called()
            self.assertEqual(load_settings(directory), stack.settings)

    def test_failed_preflight_or_ownership_never_attempts_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "state"
            stack = LocalStack(directory, initialize(directory))
            for boundary in ("validate_ownership", "preflight"):
                with (
                    self.subTest(boundary=boundary),
                    patch.object(stack, "validate_ownership", return_value={}),
                    patch.object(stack, "preflight", return_value={}),
                    patch.object(stack, boundary, side_effect=LocalFailure("REFUSED")),
                    patch.object(stack, "compose") as compose,
                    patch.object(stack, "down") as down,
                ):
                    with self.assertRaisesRegex(LocalFailure, "REFUSED"):
                        stack.up()
                    compose.assert_not_called()
                    down.assert_not_called()

    def test_launch_cleanup_refuses_changed_ownership(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "state"
            stack = LocalStack(directory, initialize(directory))
            with (
                patch.object(
                    stack,
                    "validate_ownership",
                    side_effect=[{}, LocalFailure("UNOWNED_LOCAL_RESOURCE")],
                ),
                patch.object(stack, "preflight", return_value={}),
                patch.object(
                    stack, "compose", side_effect=LocalFailure("DOCKER_COMMAND_FAILED")
                ) as compose,
            ):
                with self.assertRaisesRegex(LocalFailure, "UNOWNED_LOCAL_RESOURCE"):
                    stack.up()
                self.assertEqual(compose.call_count, 1)

    def test_ambiguous_configuration_fails_without_secret_echo(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "state"
            settings = initialize(directory)
            path = directory / "local.json"
            path.write_text('{"profile":"production",' + path.read_text()[1:])
            output = io.StringIO()
            with (
                patch("sys.argv", ["local", "check", "--state-dir", str(directory)]),
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(main(), 2)
            self.assertEqual(json.loads(output.getvalue()), {"error": "AMBIGUOUS_LOCAL_INPUT"})
            self.assertNotIn(settings.secret_key.get_secret_value(), output.getvalue())

    def test_public_digest_exception_rechecks_payload_and_exact_field(self):
        spec = importlib.util.spec_from_file_location(
            "secret_gate", ROOT / "scripts/check-secrets.py"
        )
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        case = CASES[0]
        filename = f"tests/fixtures/p01/{case}.json"
        manifest, payload = load_fixture(ROOT / "tests/fixtures/p01", case)
        line = f'  "payloadSha256": "{manifest.payloadSha256}",'
        self.assertTrue(
            gate.verified_fixture_digest(ROOT, filename, line, "Hex High Entropy String")
        )
        self.assertFalse(gate.verified_fixture_digest(ROOT, filename, line, "Secret Keyword"))
        self.assertFalse(
            gate.verified_fixture_digest(ROOT, "arbitrary.json", line, "Hex High Entropy String")
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tests/fixtures/p01/payloads").mkdir(parents=True)
            (root / filename).write_text(manifest.model_dump_json())
            (root / "tests/fixtures/p01" / manifest.sourceRef).write_bytes(payload + b"changed")
            self.assertFalse(
                gate.verified_fixture_digest(root, filename, line, "Hex High Entropy String")
            )
            fake = hashlib.sha256(b"unrelated").hexdigest()
            self.assertFalse(
                gate.verified_fixture_digest(
                    root,
                    filename,
                    line.replace(manifest.payloadSha256, fake),
                    "Hex High Entropy String",
                )
            )

    def test_remote_daemon_and_unowned_resource_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "state"
            stack = LocalStack(directory, initialize(directory))
            with patch.dict(os.environ, {"DOCKER_HOST": "tcp://remote:2375"}):
                with self.assertRaisesRegex(LocalFailure, "REMOTE_DOCKER_REFUSED"):
                    stack.local_engine()
            with (
                patch.object(stack, "local_engine", return_value={}),
                patch.object(
                    stack,
                    "docker",
                    side_effect=[
                        "shipsense-local-p01-mongodb-1\n",
                        json.dumps([{"Config": {"Labels": {"shipsense.owner": "somebody-else"}}}]),
                    ],
                ),
            ):
                with self.assertRaisesRegex(LocalFailure, "UNOWNED_LOCAL_RESOURCE"):
                    stack.down(reset=True, confirmation="shipsense-local-p01")

    def test_six_inert_payloads_have_verified_provenance(self):
        for case in CASES:
            manifest, payload = load_fixture(ROOT / "tests/fixtures/p01", case)
            self.assertEqual(json.loads(payload)["effects"], False)
            self.assertEqual(manifest.fixtureId, case)
            self.assertEqual(manifest.referenceTag, "3.1.0")

    def test_private_state_and_missing_or_empty_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "state"
            settings = initialize(directory)
            self.assertNotIn(settings.secret_key.get_secret_value(), repr(settings))
            self.assertEqual(initialize(directory), settings)
            for value in ({}, {"identities": []}, {"identities": [{"name": "anonymous"}]}):
                (directory / "s3.json").write_text(json.dumps(value))
                with self.assertRaisesRegex(LocalFailure, "PRIVATE_S3_CONFIG_REQUIRED"):
                    load_settings(directory)
            (directory / "s3.json").unlink()
            with self.assertRaisesRegex(LocalFailure, "LOCAL_CONFIG_MISSING"):
                load_settings(directory)

    def test_remote_target_and_production_profile_denied(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "state"
            settings = initialize(directory)
            config = json.loads((directory / "local.json").read_text())
            for key, value in (
                ("mongo_host", "database.example"),
                ("s3_endpoint", "https://r2.example"),
                ("database", "production"),
                ("bucket", "customer-evidence"),
                ("secret_key", ""),
                ("profile", "production"),
                ("repository", "another-checkout"),
            ):
                changed = {**config, key: value}
                (directory / "local.json").write_text(json.dumps(changed))
                with self.assertRaises(LocalFailure):
                    load_settings(directory)
            with patch.dict(os.environ, {"SHIPSENSE_PROFILE": "production"}):
                for create in (
                    MemoryQueue,
                    lambda: PrivateObjects(settings),
                    lambda: state_path(directory),
                ):
                    with self.assertRaisesRegex(LocalFailure, "LOCAL_PROFILE_REQUIRED"):
                        create()
        with self.assertRaisesRegex(LocalFailure, "UNSAFE_STATE_DIRECTORY"):
            state_path(ROOT / "credentials")

    def test_reset_confirmation_precedes_docker(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "state"
            stack = LocalStack(directory, initialize(directory))
            with patch.object(stack, "docker", side_effect=AssertionError("must not call Docker")):
                with self.assertRaisesRegex(LocalFailure, "SYNTHETIC_RESET_CONFIRMATION_REQUIRED"):
                    stack.down(reset=True, confirmation="all")

    def test_checksum_missing_scope_and_path_denial(self):
        manifest, _ = load_fixture(ROOT / "tests/fixtures/p01", CASES[0])
        data = manifest.model_dump(mode="json")
        for change in (
            {"tenantId": ""},
            {"sourceRef": "../../secret"},
            {"eventTime": "2026-11-01T00:00:00"},
            {"expiresAt": data["eventTime"]},
            {"referenceRevision": "floating"},
            {"unexpected": "value"},
        ):
            with self.assertRaises(ValidationError):
                Manifest.model_validate({**data, **change})
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "payloads").mkdir()
            (directory / f"{CASES[0]}.json").write_text(json.dumps(data))
            with self.assertRaises(LocalFailure):
                load_fixture(directory, CASES[0])
            (directory / manifest.sourceRef).write_text('{"tampered":true}')
            with self.assertRaisesRegex(LocalFailure, "FIXTURE_CHECKSUM_MISMATCH"):
                load_fixture(directory, CASES[0])
            (directory / manifest.sourceRef).write_bytes(b"x" * 32769)
            with self.assertRaisesRegex(LocalFailure, "INVALID_FIXTURE_SIZE"):
                load_fixture(directory, CASES[0])
            (directory / f"{CASES[0]}.json").write_bytes(b"x" * 16385)
            with self.assertRaisesRegex(LocalFailure, "LOCAL_INPUT_TOO_LARGE"):
                load_fixture(directory, CASES[0])


class QueueTests(unittest.IsolatedAsyncioTestCase):
    async def test_s3_probe_deadline_retains_admission_then_recovers_and_closes(self):
        with tempfile.TemporaryDirectory() as temporary:
            settings = initialize(Path(temporary) / "state")
            release = threading.Event()
            started = [threading.Event() for _ in range(4)]
            client = Mock()
            objects = None
            with patch("shipsense_local.adapters.local_s3", return_value=client):
                objects = PrivateObjects(settings)

            def block(index):
                started[index].set()
                release.wait(5)

            client.head_bucket.side_effect = lambda **kwargs: block(3)
            running = [asyncio.create_task(objects.call(lambda i=i: block(i))) for i in range(3)]
            try:
                before = asyncio.get_running_loop().time()
                self.assertFalse(await objects.probe())
                elapsed = asyncio.get_running_loop().time() - before
                self.assertGreater(elapsed, 0.8)
                self.assertLess(elapsed, 1.6)
                self.assertTrue(all(event.is_set() for event in started))
                with self.assertRaisesRegex(LocalFailure, "STORAGE_UNAVAILABLE"):
                    await objects.call(lambda: True)
                self.assertFalse(await objects.probe())
                await asyncio.wait_for(asyncio.sleep(0.01), 0.1)
                release.set()
                await asyncio.gather(*running)
                # Drain the last shielded worker through its completion callback.
                await asyncio.gather(*objects._pending)
                await asyncio.sleep(0)
                client.head_bucket.side_effect = None
                self.assertTrue(await objects.probe())
            finally:
                release.set()
                await asyncio.gather(*running, return_exceptions=True)
                await objects.close()
            client.close.assert_called_once()
            self.assertFalse(await objects.probe())
            with self.assertRaisesRegex(LocalFailure, "STORAGE_UNAVAILABLE"):
                await objects.call(lambda: True)

    async def test_s3_probe_preserves_external_cancellation_and_close_waits_for_worker(self):
        with tempfile.TemporaryDirectory() as temporary:
            settings = initialize(Path(temporary) / "state")
            release = threading.Event()
            started = threading.Event()
            client = Mock()

            def block(**kwargs):
                started.set()
                release.wait(5)

            client.head_bucket.side_effect = block
            with patch("shipsense_local.adapters.local_s3", return_value=client):
                objects = PrivateObjects(settings)
            probe = asyncio.create_task(objects.probe())
            closing = None
            try:
                async with asyncio.timeout(1):
                    while not started.is_set():
                        await asyncio.sleep(0.005)
                probe.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await probe
                closing = asyncio.create_task(objects.close())
                await asyncio.sleep(0.02)
                self.assertFalse(closing.done())
                client.close.assert_not_called()
                self.assertFalse(await objects.probe())
            finally:
                release.set()
                await asyncio.gather(probe, return_exceptions=True)
                if closing is not None:
                    await closing
                else:
                    await objects.close()
            client.close.assert_called_once()

    async def test_duplicate_reordered_poison_timeout_and_restart_loss(self):
        manifest, _ = load_fixture(ROOT / "tests/fixtures/p01", CASES[0])
        queue = MemoryQueue(1)
        first = Envelope(manifest=manifest, sequence=2)
        self.assertEqual(queue.enqueue(first), "queued")
        self.assertEqual(queue.enqueue(first), "duplicate")
        with self.assertRaisesRegex(LocalFailure, "QUEUE_CAPACITY"):
            queue.enqueue(Envelope(manifest=manifest, sequence=3))
        self.assertEqual((await queue.consume_one())["outcome"], "observed-no-effects")
        for sequence, kind, expected in (
            (1, "observe", "reordered-rejected"),
            (3, "poison", "poison-rejected"),
            (4, "timeout", "timed-out"),
        ):
            queue.enqueue(
                Envelope.model_validate({"manifest": manifest, "sequence": sequence, "kind": kind})
            )
            self.assertEqual((await queue.consume_one())["outcome"], expected)
        with self.assertRaisesRegex(LocalFailure, "QUEUE_EMPTY_TIMEOUT"):
            await queue.consume_one()
        queue.close()
        self.assertFalse(await queue.probe())
        restarted = MemoryQueue()
        self.assertEqual(restarted.enqueue(first), "queued")
        self.assertEqual((await restarted.consume_one())["outcome"], "observed-no-effects")
        restarted.close()

    async def test_expired_and_cross_scope_sequences(self):
        manifest, _ = load_fixture(ROOT / "tests/fixtures/p01", CASES[0])
        queue = MemoryQueue()
        for tenant in ("tenant-a", "tenant-b"):
            scoped = manifest.model_copy(update={"tenantId": tenant})
            queue.enqueue(Envelope(manifest=scoped, sequence=1))
            self.assertEqual((await queue.consume_one())["outcome"], "observed-no-effects")
        old = manifest.model_dump(mode="json")
        old.update(
            eventTime="2000-01-01T00:00:00Z",
            observedAt="2000-01-01T00:01:00Z",
            expiresAt="2000-01-02T00:00:00Z",
        )
        queue.enqueue(Envelope(manifest=Manifest.model_validate(old), sequence=1))
        self.assertEqual((await queue.consume_one())["outcome"], "expired-rejected")
        queue.close()

    async def test_cancelled_s3_call_retains_capacity_until_underlying_work_finishes(self):
        with tempfile.TemporaryDirectory() as temporary:
            settings = initialize(Path(temporary) / "state")
            objects = PrivateObjects(settings)
            release = threading.Event()
            running = [asyncio.create_task(objects.call(lambda: release.wait(2))) for _ in range(4)]
            await asyncio.sleep(0.03)
            for task in running:
                task.cancel()
            await asyncio.gather(*running, return_exceptions=True)
            with self.assertRaisesRegex(LocalFailure, "STORAGE_UNAVAILABLE"):
                await objects.call(lambda: True)
            # The loop remains responsive while four blocking calls are outstanding.
            await asyncio.wait_for(asyncio.sleep(0.01), 0.1)
            release.set()
            await objects.close()
            with self.assertRaisesRegex(LocalFailure, "STORAGE_UNAVAILABLE"):
                await objects.call(lambda: True)


if __name__ == "__main__":
    unittest.main()
