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
from unittest.mock import patch

from pydantic import ValidationError
from shipsense_local.adapters import PrivateObjects
from shipsense_local.cli import main
from shipsense_local.config import ROOT, LocalFailure, load_settings, state_path
from shipsense_local.fixtures import CASES, Manifest, load_fixture
from shipsense_local.queue import Envelope, MemoryQueue
from shipsense_local.stack import LocalStack, initialize


class ConfigurationTests(unittest.TestCase):
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
