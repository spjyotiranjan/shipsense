"""Hosted settings, client transport and lifespan without provider calls."""

import asyncio
import importlib.util
import os
import threading
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from shipsense_api.hosted import HostedReadiness, HostedSettings
from shipsense_api.main import create_app
from shipsense_local.config import LocalFailure


def environment():
    return {
        "SHIPSENSE_MONGODB_URI": "mongodb+srv://" + "user:synthetic-only@cluster.example.net/",
        "SHIPSENSE_MONGODB_DATABASE": "shipsense_development",
        "SHIPSENSE_R2_ENDPOINT": "https://" + "a" * 32 + ".r2.cloudflarestorage.com",
        "SHIPSENSE_R2_BUCKET": "shipsense-development",
        "SHIPSENSE_R2_ACCESS_KEY_ID": "a" * 32,
        "SHIPSENSE_R2_SECRET_ACCESS_KEY": "b" * 64,
    }


class HostedConfigurationTests(unittest.TestCase):
    def test_api_hosted_readiness_denial_recovery_and_liveness_are_independent(self):
        mongo = Mock()
        mongo.close = AsyncMock()
        read = AsyncMock(return_value=None)
        mongo.__getitem__ = Mock(return_value=Mock(fixtures=Mock(find_one=read)))
        # Windows OpenSSL needs the OS root; retain no provider configuration.
        runtime_environment = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in {"SYSTEMROOT", "WINDIR"}
        } | environment()
        with (
            patch.dict(os.environ, runtime_environment, clear=True),
            patch("shipsense_api.hosted.AsyncMongoClient", return_value=mongo),
            patch("botocore.client.BaseClient._make_api_call", return_value={}) as r2,
            self.assertLogs("shipsense.diagnostics") as logs,
            TestClient(create_app()) as api,
        ):
            self.assertEqual(api.get("/health/ready").status_code, 200)
            r2.side_effect = RuntimeError("private-hosted-denial")
            response = api.get("/health/ready")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(
                response.headers["x-request-id"], response.json()["error"]["requestId"]
            )
            self.assertEqual(api.get("/health/live").status_code, 200)
            self.assertEqual(api.get("/api/v1/version").status_code, 200)
            r2.side_effect = None
            self.assertEqual(api.get("/health/ready").status_code, 200)
            self.assertTrue(all(call.args[0] == "HeadBucket" for call in r2.call_args_list))
            self.assertNotIn("private-hosted-denial", response.text + str(logs.output))
            self.assertNotIn("cluster.example.net", response.text + str(logs.output))
        mongo.close.assert_awaited_once()

    def test_missing_placeholders_and_unsafe_inputs_refuse_before_clients(self):
        invalid = [({},), ({"SHIPSENSE_MONGODB_DATABASE": "admin"},)]
        uri = environment()["SHIPSENSE_MONGODB_URI"]
        for query in (
            "tls=false",
            "ssl=false",
            "tlsInsecure=true",
            "tlsAllowInvalidCertificates=true",
            "tlsCAFile=/private/file",
            "proxyHost=other.invalid",
            "connectTimeoutMS=0",
            "authSource=admin&authSource=other",
            "authSource=admin&AUTHSOURCE=other",
        ):
            invalid.append(({"SHIPSENSE_MONGODB_URI": uri + "?" + query},))
        for endpoint in (
            "http://" + "a" * 32 + ".r2.cloudflarestorage.com",
            "https://r2.cloudflarestorage.com.evil.invalid",
            "https://" + "a" * 32 + ".r2.cloudflarestorage.com/?redirect=other",
            "http://127.0.0.1:38333",
            "https://user@" + "a" * 32 + ".r2.cloudflarestorage.com",
        ):
            invalid.append(({"SHIPSENSE_R2_ENDPOINT": endpoint},))
        for key, value in (
            ("SHIPSENSE_MONGODB_URI", "mongodb://" + "user:synthetic-only@127.0.0.1/"),
            ("SHIPSENSE_MONGODB_URI", uri.replace("user", "<username>")),
            ("SHIPSENSE_MONGODB_URI", uri.replace("user", "%0auser")),
            ("SHIPSENSE_MONGODB_DATABASE", "invalid/database"),
            ("SHIPSENSE_R2_BUCKET", "bad.bucket"),
            ("SHIPSENSE_R2_ACCESS_KEY_ID", "replace-with-key"),
            ("SHIPSENSE_R2_SECRET_ACCESS_KEY", ""),
        ):
            invalid.append(({key: value},))
        for (changed,) in invalid:
            values = {} if not changed else environment() | changed
            with (
                self.subTest(changed=tuple(changed)),
                patch.dict(os.environ, values, clear=True),
                patch("shipsense_api.hosted.HostedClients") as clients,
                self.assertLogs("shipsense.diagnostics") as logs,
                TestClient(create_app()) as api,
            ):
                response = api.get("/health/ready")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(api.get("/health/live").status_code, 200)
                self.assertEqual(api.get("/api/v1/version").status_code, 200)
                self.assertNotIn("cluster.example.net", response.text + str(logs.output))
                self.assertNotIn("synthetic-only", response.text + str(logs.output))
                clients.assert_not_called()

    def test_example_is_nonfunctional_and_legacy_state_is_never_fallback(self):
        example = Path(__file__).resolve().parents[3] / ".env.example"
        values = dict(
            line.split("=", 1)
            for line in example.read_text().splitlines()
            if line and not line.startswith("#")
        )
        self.assertTrue(all(not values[key] for key in environment()))
        with self.assertRaisesRegex(LocalFailure, "^HOSTED_CONFIG_INVALID$"):
            HostedSettings.from_environment(values)
        for legacy_state in ("//never-inspect.invalid/state", "unused-private-state"):
            values = {"SHIPSENSE_LOCAL_STATE_DIR": legacy_state}
            with (
                patch.dict(os.environ, values, clear=True),
                TestClient(create_app()) as api,
            ):
                self.assertEqual(api.get("/health/ready").status_code, 503)

    def test_database_base_and_profile_validate_the_final_target_before_clients(self):
        for base in ("ShipSense", "shipsense-local", "a" * 57):
            settings = HostedSettings.from_environment(
                environment() | {"SHIPSENSE_MONGODB_DATABASE": base, "SHIPSENSE_PROFILE": "local"}
            )
            self.assertEqual(settings.effective_database, base + "-local")
        for changed in (
            {"SHIPSENSE_MONGODB_DATABASE": "a" * 58},
            {"SHIPSENSE_MONGODB_DATABASE": "admin"},
            {"SHIPSENSE_MONGODB_DATABASE": "base/other"},
            {"SHIPSENSE_PROFILE": ""},
            {"SHIPSENSE_PROFILE": "../other"},
            {"SHIPSENSE_PROFILE": "production"},
        ):
            with self.subTest(fields=tuple(changed)):
                with self.assertRaisesRegex(LocalFailure, "^HOSTED_CONFIG_INVALID$"):
                    HostedSettings.from_environment(environment() | changed)

    def test_srv_and_standard_replica_strings_keep_secrets_redacted(self):
        for uri in (
            environment()["SHIPSENSE_MONGODB_URI"],
            "mongodb://" + "user:synthetic-only@one.example.net:27017,two.example.net:27017/"
            "?replicaSet=rs0&tls=true&authSource=admin&retryWrites=true&w=majority&appName=ShipSense",
        ):
            settings = HostedSettings.from_environment(
                environment() | {"SHIPSENSE_MONGODB_URI": uri}
            )
            self.assertNotIn("synthetic-only", repr(settings))
            self.assertNotIn("b" * 64, repr(settings))


class HostedLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_sdk_construction_and_close_are_lazy_without_dns_or_connections(self):
        for uri in (
            environment()["SHIPSENSE_MONGODB_URI"],
            environment()["SHIPSENSE_MONGODB_URI"].replace("mongodb+srv://", "mongodb://"),
        ):
            with (
                patch("socket.getaddrinfo", side_effect=AssertionError("DNS reached")) as dns,
                patch(
                    "socket.socket.connect", side_effect=AssertionError("network reached")
                ) as tcp,
            ):
                runtime = await HostedReadiness.from_environment(
                    environment() | {"SHIPSENSE_MONGODB_URI": uri}
                )
                self.assertEqual(runtime.clients.mongo.options.pool_options.max_pool_size, 4)
                await runtime.close()
                dns.assert_not_called()
                tcp.assert_not_called()

    async def test_tls_private_clients_probes_failure_recovery_and_shutdown(self):
        mongo = Mock()
        mongo.close = AsyncMock()
        read = AsyncMock(return_value=None)
        mongo.__getitem__ = Mock(return_value=Mock(fixtures=Mock(find_one=read)))
        with patch("shipsense_api.hosted.AsyncMongoClient", return_value=mongo) as factory:
            runtime = await HostedReadiness.from_environment(environment())
        mongo.__getitem__.assert_called_once_with("shipsense_development-local")
        options = factory.call_args.kwargs
        self.assertTrue(options["tls"])
        self.assertFalse(options["tlsAllowInvalidCertificates"])
        self.assertFalse(options["tlsAllowInvalidHostnames"])
        self.assertFalse(options["connect"])
        self.assertLessEqual(options["timeoutMS"], 1000)
        self.assertEqual(options["maxPoolSize"], 4)
        s3 = runtime.clients.objects._client
        self.assertEqual(s3.meta.region_name, "auto")
        self.assertEqual(s3.meta.endpoint_url, environment()["SHIPSENSE_R2_ENDPOINT"])
        self.assertEqual(s3.meta.config.retries["total_max_attempts"], 1)
        self.assertEqual(s3.meta.config.proxies, {})
        self.assertTrue(s3._endpoint.http_session._verify)
        with patch.object(s3, "head_bucket", return_value={}) as head:
            self.assertTrue(await runtime.gate.ready())
            self.assertEqual(head.call_args.kwargs, {"Bucket": "shipsense-development"})
            self.assertEqual(read.call_args.args[0]["providerObjectId"], "hosted-probe")
            self.assertEqual(read.call_args.args[1], {"_id": 1})
            head.side_effect = RuntimeError("private-provider-failure")
            self.assertFalse(await runtime.gate.ready())
            head.side_effect = None
            self.assertTrue(await runtime.gate.ready())
            read.side_effect = RuntimeError("private-denial")
            self.assertFalse(await runtime.gate.ready())
            read.side_effect = None
            self.assertTrue(await runtime.gate.ready())
        await runtime.close()
        await runtime.close()
        mongo.close.assert_awaited_once()
        self.assertFalse(await runtime.queue_probe())

    async def test_partial_r2_construction_closes_mongo_without_network(self):
        mongo = Mock()
        mongo.__getitem__ = Mock()
        mongo.close = AsyncMock()
        with (
            patch("shipsense_api.hosted.AsyncMongoClient", return_value=mongo),
            patch("shipsense_api.hosted.private_s3", side_effect=RuntimeError("factory failed")),
        ):
            with self.assertRaises(RuntimeError):
                await HostedReadiness.from_environment(environment())
        mongo.close.assert_awaited_once()

    async def test_cancellation_retains_capacity_and_shutdown_drains_owned_workers(self):
        mongo = Mock()
        mongo.__getitem__ = Mock()
        mongo.close = AsyncMock()
        with patch("shipsense_api.hosted.AsyncMongoClient", return_value=mongo):
            runtime = await HostedReadiness.from_environment(environment())
        entered = threading.Event()
        release = threading.Event()

        def slow():
            entered.set()
            release.wait(3)

        work = asyncio.create_task(runtime.clients.objects.call(slow))
        await asyncio.to_thread(entered.wait, 1)
        work.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await work
        self.assertEqual(len(runtime.clients.objects._pending), 1)
        close = asyncio.create_task(runtime.close())
        await asyncio.sleep(0.02)
        close.cancel()
        await asyncio.sleep(0.02)
        self.assertFalse(close.done())
        self.assertFalse(await runtime.queue_probe())
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await close
        self.assertFalse(runtime.clients.objects._pending)
        mongo.close.assert_awaited_once()


class HostedIntegrationBoundaryTests(unittest.IsolatedAsyncioTestCase):
    def smoke_module(self):
        path = Path(__file__).resolve().parents[3] / "scripts/integration-smoke.py"
        spec = importlib.util.spec_from_file_location("hosted_smoke", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    async def test_hosted_command_missing_config_fails_before_process_or_provider_access(self):
        smoke = self.smoke_module()
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(smoke, "verify_hosted_access", new_callable=AsyncMock) as probe,
            patch.object(smoke, "start_api") as api,
        ):
            with self.assertRaisesRegex(LocalFailure, "^HOSTED_CONFIG_INVALID$"):
                smoke.smoke(Path("unused"), hosted=True, fail_upstream=False)
            probe.assert_not_called()
            api.assert_not_called()

    async def test_no_hosted_or_agent_secrets_reach_web_browser_environment(self):
        smoke = self.smoke_module()
        marker = "synthetic-private-marker"
        values = environment() | {
            "PAPERCLIP_API_KEY": marker,
            "AWS_SECRET_ACCESS_KEY": marker,
            "HTTPS_PROXY": marker,
            "SHIPSENSE_LOCAL_STATE_DIR": "//never-inspect.invalid/share",
            "PATH": "safe-path",
        }
        with patch.dict(os.environ, values, clear=True):
            result = smoke.clean_environment()
        self.assertEqual(result["PATH"], "safe-path")
        for key in values.keys() - {"PATH"}:
            self.assertNotIn(key, result)

    async def test_hosted_read_and_bucket_denials_close_clients_without_writes(self):
        smoke = self.smoke_module()
        runtime = Mock()
        runtime.clients.mongo_probe = AsyncMock(return_value=True)
        runtime.clients.objects.probe = AsyncMock(return_value=True)
        runtime.close = AsyncMock()
        client = Mock()
        client.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}, "ResponseMetadata": {"HTTPStatusCode": 403}},
            "ListObjectsV2",
        )
        with (
            patch.object(smoke.HostedReadiness, "from_environment", return_value=runtime),
            patch.object(smoke, "private_s3", return_value=client) as factory,
        ):
            await smoke.verify_hosted_access(environment())
        runtime.clients.mongo_probe.assert_awaited_once()
        runtime.clients.objects.probe.assert_awaited_once()
        runtime.close.assert_awaited_once()
        self.assertEqual(client.list_objects_v2.call_count, 2)
        self.assertTrue(
            all(
                call.kwargs == {"Bucket": "shipsense-development", "MaxKeys": 0}
                for call in client.list_objects_v2.call_args_list
            )
        )
        self.assertEqual(client.close.call_count, 2)
        self.assertEqual(
            [call.kwargs["unsigned"] for call in factory.call_args_list], [True, False]
        )
        self.assertEqual({call[0] for call in client.method_calls}, {"list_objects_v2", "close"})

    async def test_transport_failure_cannot_count_as_anonymous_denial_or_skip_close(self):
        smoke = self.smoke_module()
        runtime = Mock()
        runtime.clients.mongo_probe = AsyncMock(return_value=True)
        runtime.clients.objects.probe = AsyncMock(return_value=True)
        runtime.close = AsyncMock()
        client = Mock()
        client.list_objects_v2.side_effect = OSError("private-provider-error")
        with (
            patch.object(smoke.HostedReadiness, "from_environment", return_value=runtime),
            patch.object(smoke, "private_s3", return_value=client),
        ):
            with self.assertRaisesRegex(LocalFailure, "^STORAGE_UNAVAILABLE$"):
                await smoke.verify_hosted_access(environment())
        runtime.close.assert_awaited_once()
        client.close.assert_called_once()

    async def test_r2_authentication_errors_are_distinct_from_arbitrary_http_failures(self):
        smoke = self.smoke_module()
        for status, code, message, accepted in (
            (400, "InvalidArgument", "Authorization", True),
            (400, "InvalidArgument", "Invalid bucket", False),
            (403, "Unknown", "Unknown", False),
            (503, "ServiceUnavailable", "Unavailable", False),
            (401, "Unauthorized", "Unauthorized", True),
        ):
            with self.subTest(status=status, code=code, accepted=accepted):
                runtime = Mock()
                runtime.clients.mongo_probe = AsyncMock(side_effect=[False, True])
                runtime.clients.objects.probe = AsyncMock(return_value=True)
                runtime.close = AsyncMock()
                client = Mock()
                client.list_objects_v2.side_effect = [
                    ClientError(
                        {
                            "Error": {"Code": code, "Message": message},
                            "ResponseMetadata": {"HTTPStatusCode": status},
                        },
                        "ListObjectsV2",
                    ),
                    ClientError(
                        {
                            "Error": {"Code": "Unauthorized"},
                            "ResponseMetadata": {"HTTPStatusCode": 401},
                        },
                        "ListObjectsV2",
                    ),
                ]
                with (
                    patch.object(smoke.HostedReadiness, "from_environment", return_value=runtime),
                    patch.object(smoke, "private_s3", return_value=client),
                    patch.object(smoke.asyncio, "sleep", new_callable=AsyncMock),
                ):
                    if accepted:
                        await smoke.verify_hosted_access(environment())
                    else:
                        with self.assertRaisesRegex(LocalFailure, "^HOSTED_R2_DENIAL_NOT_PROVED$"):
                            await smoke.verify_hosted_access(environment())
                runtime.close.assert_awaited_once()
                self.assertEqual(client.close.call_count, 2 if accepted else 1)

    async def test_persistent_mongo_failure_is_bounded_and_closes_without_r2_reads(self):
        smoke = self.smoke_module()
        runtime = Mock()
        runtime.clients.mongo_probe = AsyncMock(return_value=False)
        runtime.clients.objects.probe = AsyncMock()
        runtime.close = AsyncMock()
        with (
            patch.object(smoke.HostedReadiness, "from_environment", return_value=runtime),
            patch.object(smoke.asyncio, "sleep", new_callable=AsyncMock),
        ):
            with self.assertRaisesRegex(LocalFailure, "^HOSTED_MONGODB_READ_FAILED$"):
                await smoke.verify_hosted_access(environment())
        self.assertEqual(runtime.clients.mongo_probe.await_count, 3)
        runtime.clients.objects.probe.assert_not_awaited()
        runtime.close.assert_awaited_once()
