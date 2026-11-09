"""Real local adapters and app lifespan. Requires explicit SHIPSENSE_TEST_STATE."""

import asyncio
import os
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from shipsense_api.diagnostics import ApiError
from shipsense_api.main import create_app
from shipsense_local.config import load_settings
from shipsense_local.queue import MemoryQueue
from shipsense_local.stack import LocalStack


@unittest.skipUnless(
    os.environ.get("SHIPSENSE_TEST_STATE"), "requires explicit owned local runtime"
)
class ReadinessIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = Path(os.environ["SHIPSENSE_TEST_STATE"])
        self.stack = LocalStack(self.directory, load_settings(self.directory))
        await asyncio.to_thread(self.stack.validate_ownership)
        self.enterContext(
            patch.dict(os.environ, {"SHIPSENSE_LOCAL_STATE_DIR": str(self.directory)})
        )
        self.app = create_app()
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.addAsyncCleanup(self.close_lifespan)
        self.runtime = self.app.state.local_runtime
        self.assertIsNotNone(self.runtime)
        self.http = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url="http://local"
        )
        self.addAsyncCleanup(self.http.aclose)
        await self.wait_ready()

    async def close_lifespan(self):
        await self.lifespan.__aexit__(None, None, None)
        self.assertIsNone(self.app.state.local_runtime)
        self.assertFalse(await self.app.state.readiness_gate.ready())
        self.assertFalse(self.runtime.clients.objects._pending)

    async def wait_ready(self):
        async with asyncio.timeout(15):
            while (await self.http.get("/health/ready")).status_code != 200:
                await asyncio.sleep(0.15)

    async def assert_independent(self):
        for route in ("/health/live", "/api/v1/version", "/docs", "/openapi.json"):
            self.assertEqual((await self.http.get(route)).status_code, 200)

    async def test_real_dependency_stop_recovery_and_contracts(self):
        for service in ("mongodb", "storage"):
            await asyncio.to_thread(self.stack.validate_ownership)
            await asyncio.to_thread(self.stack.docker, "stop", f"shipsense-local-p01-{service}-1")
            try:
                start = time.monotonic()
                response = await self.http.get(
                    "/health/ready", headers={"X-Request-ID": "outage-1"}
                )
                self.assertLess(time.monotonic() - start, 1.8)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.headers["cache-control"], "no-store")
                error = ApiError.model_validate(response.json()).error
                self.assertEqual(error.requestId, "outage-1")
                schema = (await self.http.get("/openapi.json")).json()
                example = schema["paths"]["/health/ready"]["get"]["responses"]["503"]["content"][
                    "application/json"
                ]["example"]
                example["error"]["requestId"] = "outage-1"
                self.assertEqual(response.json(), example)
                await self.assert_independent()
                results = await asyncio.gather(*(self.http.get("/health/ready") for _ in range(12)))
                self.assertTrue(all(result.status_code == 503 for result in results))
            finally:
                await asyncio.to_thread(self.stack.validate_ownership)
                await asyncio.to_thread(self.stack.compose, "start", service)
            await self.wait_ready()

    async def test_same_process_queue_unavailable_recovery_and_restart(self):
        self.runtime.queue.close()
        self.assertEqual((await self.http.get("/health/ready")).status_code, 503)
        await self.assert_independent()
        self.runtime.queue = MemoryQueue()
        await self.wait_ready()
        original = self.runtime
        await self.lifespan.__aexit__(None, None, None)
        self.assertFalse(await original.queue_probe())
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.runtime = self.app.state.local_runtime
        self.assertIsNot(self.runtime, original)
        self.assertIsNot(self.runtime.queue, original.queue)
        await self.wait_ready()

    async def test_slow_real_storage_deadline_capacity_cancel_and_recovery(self):
        objects = self.runtime.clients.objects
        original = objects._client.head_bucket
        release = threading.Event()
        started = threading.Event()
        active = peak = 0
        lock = threading.Lock()

        def delayed(**kwargs):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            started.set()
            try:
                release.wait(2)
                return original(**kwargs)
            finally:
                with lock:
                    active -= 1

        with patch.object(objects._client, "head_bucket", side_effect=delayed):
            try:
                start = time.monotonic()
                results = await asyncio.gather(*(self.http.get("/health/ready") for _ in range(12)))
                self.assertLess(time.monotonic() - start, 1.8)
                self.assertTrue(all(result.status_code == 503 for result in results))
                self.assertEqual(peak, 4)
                self.assertEqual(len(objects._pending), 4)
                await self.assert_independent()
            finally:
                release.set()
                await asyncio.gather(*objects._pending, return_exceptions=True)
            await self.wait_ready()
            release.clear()
            started.clear()
            pending = asyncio.create_task(self.runtime.gate.ready())
            await asyncio.to_thread(started.wait, 1)
            pending.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await pending
            self.assertEqual(len(objects._pending), 1)
            release.set()
            await asyncio.gather(*objects._pending, return_exceptions=True)
        await self.wait_ready()
