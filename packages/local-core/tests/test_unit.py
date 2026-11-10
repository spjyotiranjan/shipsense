"""Inert fixture integrity, bounded storage concurrency and no-effect queue behavior."""

import asyncio
import hashlib
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

from pydantic import ValidationError
from shipsense_local.adapters import BoundedObjects
from shipsense_local.config import ROOT, LocalFailure
from shipsense_local.fixtures import CASES, Manifest, load_fixture
from shipsense_local.queue import Envelope, MemoryQueue


class FixtureTests(unittest.TestCase):
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

    def test_six_inert_payloads_have_verified_provenance(self):
        for case in CASES:
            manifest, payload = load_fixture(ROOT / "tests/fixtures/p01", case)
            self.assertEqual(json.loads(payload)["effects"], False)
            self.assertEqual(manifest.fixtureId, case)
            self.assertEqual(manifest.referenceTag, "3.1.0")

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
        with tempfile.TemporaryDirectory():
            release = threading.Event()
            started = [threading.Event() for _ in range(4)]
            client = Mock()
            objects = None
            objects = BoundedObjects("synthetic-test", client)

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
        with tempfile.TemporaryDirectory():
            release = threading.Event()
            started = threading.Event()
            client = Mock()

            def block(**kwargs):
                started.set()
                release.wait(5)

            client.head_bucket.side_effect = block
            objects = BoundedObjects("synthetic-test", client)
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
        with tempfile.TemporaryDirectory():
            objects = BoundedObjects("synthetic-test", Mock())
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
