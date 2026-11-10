"""Real owned Mongo/S3 operations. Set SHIPSENSE_TEST_STATE after local:up."""

import asyncio
import hashlib
import os
import stat
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
from pymongo import AsyncMongoClient
from pymongo.errors import OperationFailure
from shipsense_api.main import create_app
from shipsense_local.adapters import LocalClients, local_s3
from shipsense_local.cli import private_access
from shipsense_local.config import ROOT, LocalFailure, load_settings
from shipsense_local.fixtures import CASES, FixtureStore, load_fixture, seed_all
from shipsense_local.stack import LocalStack


@unittest.skipUnless(
    os.environ.get("SHIPSENSE_TEST_STATE"), "requires explicit owned local runtime"
)
class AdapterIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = Path(os.environ["SHIPSENSE_TEST_STATE"])
        self.settings = load_settings(self.directory)
        self.stack = LocalStack(self.directory, self.settings, project=self.settings.project)
        await asyncio.to_thread(self.stack.validate_ownership)
        self.clients = LocalClients(self.settings)
        self.store = FixtureStore(self.clients)
        await self.store.initialize()
        manifest, self.payload = load_fixture(ROOT / "tests/fixtures/p01", CASES[0])
        self.manifest = manifest.model_copy(update={"projectId": "integration-" + uuid4().hex})

    async def asyncTearDown(self):
        await self.clients.close()

    async def test_authenticated_access_and_real_denials(self):
        self.stack.validate_ownership()
        permissions = self.stack.docker(
            "exec",
            f"{self.settings.project}-mongodb-1",
            "stat",
            "-c",
            "%a %U %G",
            "/run/shipsense",
            "/run/shipsense/mongo-root.txt",
            "/run/shipsense/mongo-app.json",
        )
        self.assertEqual(
            permissions.splitlines(),
            ["700 mongodb mongodb", "600 mongodb mongodb", "600 mongodb mongodb"],
        )
        filesystem = self.stack.docker(
            "exec",
            f"{self.settings.project}-mongodb-1",
            "stat",
            "-f",
            "-c",
            "%T",
            "/run/shipsense",
        )
        self.assertEqual(filesystem.strip(), "tmpfs")
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o700)
            for name in ("local.json", "mongo-root.txt", "mongo-app.json", "s3.json"):
                self.assertEqual(stat.S_IMODE((self.directory / name).stat().st_mode), 0o600)
        self.assertTrue(await self.clients.mongo_probe())
        self.assertTrue(await self.clients.objects.probe())
        await private_access(self.settings, self.clients)
        for auth in (
            {},
            {
                "username": self.settings.mongo_user,
                "password": uuid4().hex,
                "authSource": self.settings.database,
            },
        ):
            client = AsyncMongoClient(
                "127.0.0.1", 37017, serverSelectionTimeoutMS=500, timeoutMS=800, **auth
            )
            try:
                with self.assertRaises(OperationFailure):
                    await client[self.settings.database].fixtures.find_one(
                        {"tenantId": "synthetic-tenant"}
                    )
            finally:
                await client.close()
        # The application identity cannot retrieve admin users.
        with self.assertRaises(OperationFailure):
            await self.clients.mongo.admin.command("usersInfo", 1)
        # Host cloud profiles/paths must never change local behavior.
        with patch.dict(
            os.environ,
            {
                "AWS_PROFILE": "must-not-load-host-profile",
                "AWS_CONFIG_FILE": "must-not-read-host-config",
            },
        ):
            client = local_s3(self.settings)
            try:
                await self.clients.objects.call(
                    lambda: client.head_bucket(Bucket=self.settings.bucket)
                )
            finally:
                client.close()

    async def test_repeated_seed_is_noop_and_scoped_metadata(self):
        first = await seed_all(self.clients)
        second = await seed_all(self.clients)
        self.assertEqual(sum(first.values()), 6)
        self.assertEqual(second, {"inserted": 0, "unchanged": 6})
        self.assertEqual(
            await self.store.collection.count_documents(
                {
                    "tenantId": "synthetic-tenant",
                    "projectId": "synthetic-astronomy",
                    "serviceId": "product-catalog",
                    "environment": "local",
                    "provider": "synthetic",
                    "providerVersion": "v1",
                }
            ),
            6,
        )

    async def test_concurrent_identical_and_conflicting_writes_preserve_winner(self):
        # S3 has four-call admission; use two concurrent writers to test its real CAS.
        identical = await asyncio.gather(
            *(self.store.seed(self.manifest, self.payload) for _ in range(2))
        )
        self.assertEqual(sorted(identical), ["inserted", "unchanged"])
        other_payload = b'{"synthetic":"conflicting-evidence","effects":false}\n'
        other = self.manifest.model_copy(
            update={"payloadSha256": hashlib.sha256(other_payload).hexdigest()}
        )
        with self.assertRaisesRegex(LocalFailure, "FIXTURE_VERSION_CONFLICT"):
            await self.store.seed(other, other_payload)
        self.assertEqual(await self.store.collection.count_documents(self.manifest.scope()), 1)
        self.assertEqual(
            (await self.store.collection.find_one(self.manifest.scope()))["payloadSha256"],
            self.manifest.payloadSha256,
        )
        await self.clients.objects.read_verified(
            self.manifest.object_key(), self.manifest.payloadSha256
        )

        # Race two hashes before either metadata row exists, exercising unique-index CAS.
        racing = self.manifest.model_copy(update={"providerVersion": "race-v2"})
        challenger = racing.model_copy(update={"payloadSha256": other.payloadSha256})
        outcomes = await asyncio.gather(
            self.store.seed(racing, self.payload),
            self.store.seed(challenger, other_payload),
            return_exceptions=True,
        )
        self.assertEqual(sum(value == "inserted" for value in outcomes), 1)
        self.assertEqual(sum(isinstance(value, LocalFailure) for value in outcomes), 1)
        winner = await self.store.collection.find_one(racing.scope())
        self.assertIn(winner["payloadSha256"], (racing.payloadSha256, challenger.payloadSha256))
        self.assertEqual(await self.store.collection.count_documents(racing.scope()), 1)

    async def test_cross_scope_no_metadata_or_object_alias(self):
        await self.store.seed(self.manifest, self.payload)
        for changes in (
            {"tenantId": "another-synthetic-tenant"},
            {"projectId": self.manifest.projectId + "-other"},
        ):
            scoped = self.manifest.model_copy(update=changes)
            self.assertNotEqual(scoped.object_key(), self.manifest.object_key())
            self.assertIsNone(await self.store.collection.find_one(scoped.scope()))
            self.assertEqual(await self.store.seed(scoped, self.payload), "inserted")
            self.assertEqual(await self.store.collection.count_documents(scoped.scope()), 1)

    async def test_object_first_interruption_retry_and_no_checksum_overwrite(self):
        # Interrupt the actual store after its real S3 write, before Mongo insert.
        with patch.object(
            self.store.collection, "insert_one", new=AsyncMock(side_effect=RuntimeError)
        ):
            with self.assertRaises(RuntimeError):
                await self.store.seed(self.manifest, self.payload)
        self.assertIsNone(await self.store.collection.find_one(self.manifest.scope()))
        await self.clients.objects.read_verified(
            self.manifest.object_key(), self.manifest.payloadSha256
        )
        self.assertEqual(await self.store.seed(self.manifest, self.payload), "inserted")
        self.assertEqual(await self.store.seed(self.manifest, self.payload), "unchanged")
        bad = self.manifest.model_copy(update={"providerVersion": "bad-checksum-v2"})
        with self.assertRaisesRegex(LocalFailure, "FIXTURE_CHECKSUM_MISMATCH"):
            await self.store.seed(bad, b"tampered")
        self.assertIsNone(await self.store.collection.find_one(bad.scope()))

    async def test_missing_and_corrupt_existing_objects_preserve_metadata_and_conflict(self):
        await self.store.seed(self.manifest, self.payload)
        client = self.clients.objects._client
        key = self.manifest.object_key()
        await self.clients.objects.call(
            lambda: client.delete_object(Bucket=self.settings.bucket, Key=key)
        )
        with self.assertRaises(LocalFailure):
            await self.store.seed(self.manifest, self.payload)
        self.assertEqual(await self.store.collection.count_documents(self.manifest.scope()), 1)
        await self.clients.objects.call(
            lambda: client.put_object(Bucket=self.settings.bucket, Key=key, Body=b"corrupt")
        )
        with self.assertRaisesRegex(LocalFailure, "OBJECT_CHECKSUM_MISMATCH"):
            await self.store.seed(self.manifest, self.payload)
        with self.assertRaisesRegex(LocalFailure, "OBJECT_CHECKSUM_MISMATCH"):
            await self.clients.objects.write_verified(
                key, self.payload, self.manifest.payloadSha256
            )
        # Conditional S3 writes cannot overwrite the deliberately injected corruption.
        self.assertEqual(
            await self.clients.objects.call(lambda: self.clients.objects._read(key)), b"corrupt"
        )

    async def test_real_bounded_dependency_outage_recovery_and_liveness_independence(self):
        app = create_app()  # Existing API stays unwired; readiness remains safe 503.
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://local"
        ) as api:
            for service, probe in (
                ("mongodb", self.clients.mongo_probe),
                ("storage", self.clients.objects.probe),
            ):
                self.assertTrue(await probe())
                await asyncio.to_thread(self.stack.compose, "stop", service)
                try:
                    started = time.monotonic()
                    results, live = await asyncio.gather(
                        asyncio.gather(*(probe() for _ in range(8))), api.get("/health/live")
                    )
                    self.assertFalse(any(results))
                    self.assertLess(time.monotonic() - started, 3)
                    self.assertEqual(live.status_code, 200)
                    self.assertEqual((await api.get("/health/ready")).status_code, 503)
                finally:
                    await asyncio.to_thread(self.stack.compose, "start", service)
                async with asyncio.timeout(30):
                    while not await probe():
                        await asyncio.sleep(0.3)
                self.assertEqual((await api.get("/health/live")).status_code, 200)


if __name__ == "__main__":
    unittest.main()
