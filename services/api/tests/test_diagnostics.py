import asyncio
import logging
import time
import unittest
from datetime import datetime
from unittest.mock import patch

from fastapi import Query
from fastapi.testclient import TestClient
from pydantic import ValidationError
from shipsense_api.diagnostics import ApiError, ReadinessGate, VersionResponse
from shipsense_api.main import create_app


class DiagnosticTests(unittest.TestCase):
    def test_all_error_codes_are_canonical_and_unknown_codes_reject(self):
        codes = {
            "DEPENDENCY_UNAVAILABLE",
            "INVALID_REQUEST",
            "INTERNAL_ERROR",
            "API_UNAVAILABLE",
            "API_TIMEOUT",
            "UPSTREAM_CONTRACT_INVALID",
        }
        schema = create_app().openapi()
        self.assertEqual(
            set(schema["components"]["schemas"]["ErrorDetail"]["properties"]["code"]["enum"]), codes
        )
        for code in codes:
            ApiError.model_validate(
                {
                    "error": {
                        "code": code,
                        "message": "Safe error.",
                        "requestId": "test-1",
                        "retryable": True,
                    }
                }
            )
        for override in ({"code": "UNKNOWN"}, {"message": "x" * 161}, {"requestId": "x" * 65}):
            with self.assertRaises(ValidationError):
                ApiError.model_validate(
                    {
                        "error": {
                            "code": "API_TIMEOUT",
                            "message": "Safe error.",
                            "requestId": "test-1",
                            "retryable": True,
                        }
                        | override
                    }
                )

    def test_credential_free_success_freshness_and_no_cache(self):
        with patch.dict("os.environ", {}, clear=True), TestClient(create_app()) as client:
            first = client.get("/api/v1/version", headers={"X-Request-ID": "req-local-001"})
            second = client.get("/api/v1/version")
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.headers["x-request-id"], "req-local-001")
            body = VersionResponse.model_validate(first.json())
            self.assertEqual(body.version, "0.1.0-dev")
            self.assertIsNotNone(datetime.fromisoformat(first.json()["observedAt"]).tzinfo)
            self.assertNotEqual(first.json()["observedAt"], second.json()["observedAt"])
            self.assertEqual(client.get("/health/live").json(), {"status": "alive"})
            for response in (first, second, client.get("/health/live")):
                self.assertEqual(response.headers["cache-control"], "no-store")

    def test_missing_dependencies_never_ready_but_liveness_survives(self):
        with TestClient(create_app()) as client:
            for _ in range(2):
                response = client.get("/health/ready")
                self.assertEqual(response.status_code, 503)
                error = ApiError.model_validate(response.json()).error
                self.assertEqual(error.code, "DEPENDENCY_UNAVAILABLE")
                self.assertTrue(error.retryable)
                self.assertEqual(error.requestId, response.headers["x-request-id"])
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(client.get("/health/live").status_code, 200)

    def test_invalid_header_bounds_duplicates_and_safe_validation(self):
        app = create_app()

        @app.get("/test-input")
        async def input_boundary(value: int = Query(ge=0, le=10)):
            return {"value": value}

        with TestClient(app) as client:
            for value in ("", "x" * 65, "secret/value", "contains space"):
                response = client.get("/api/v1/version", headers={"X-Request-ID": value})
                self.assertEqual(response.status_code, 422)
                error = ApiError.model_validate(response.json()).error
                self.assertEqual(error.code, "INVALID_REQUEST")
                self.assertFalse(error.retryable)
                self.assertRegex(error.requestId, r"^req-[a-f0-9]{32}$")
            self.assertEqual(
                client.get("/api/v1/version", headers={"X-Request-ID": "x" * 64}).status_code, 200
            )
            self.assertEqual(
                client.get(
                    "/api/v1/version", headers=[("X-Request-ID", "a"), ("X-Request-ID", "b")]
                ).status_code,
                422,
            )
            response = client.get("/test-input?value=private-rejected-value")
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("private-rejected-value", response.text)
            ApiError.model_validate(response.json())

    def test_internal_and_http_errors_are_redacted_in_body_and_application_log(self):
        app = create_app()

        @app.get("/test-error")
        async def fail():
            raise RuntimeError("private-dsn-value")

        with TestClient(app, raise_server_exceptions=False) as client:
            with self.assertLogs("shipsense.diagnostics", logging.INFO) as logs:
                response = client.get("/test-error?secret=private-query-value")
                missing = client.get("/private-path-value")
            self.assertEqual(response.status_code, 500)
            self.assertEqual(ApiError.model_validate(response.json()).error.code, "INTERNAL_ERROR")
            self.assertEqual(missing.status_code, 404)
            for private in ("private-dsn-value", "private-query-value", "private-path-value"):
                self.assertNotIn(private, response.text + missing.text + str(logs.output))

    def test_schema_examples_match_models_and_custom_errors(self):
        with TestClient(create_app()) as client:
            schema = client.get("/openapi.json").json()
            for route in ("/api/v1/version", "/health/live", "/health/ready"):
                responses = schema["paths"][route]["get"]["responses"]
                for status in ("422", "500"):
                    content = responses[status]["content"]["application/json"]
                    self.assertEqual(content["schema"]["$ref"], "#/components/schemas/ApiError")
                    ApiError.model_validate(content["example"])
            ready_error = schema["paths"]["/health/ready"]["get"]["responses"]["503"]["content"][
                "application/json"
            ]["example"]
            actual = client.get("/health/ready", headers={"X-Request-ID": "req-local-001"})
            self.assertEqual(actual.json(), ready_error)
            self.assertEqual(client.get("/docs").status_code, 200)
            success = schema["paths"]["/api/v1/version"]["get"]["responses"]["200"]["content"][
                "application/json"
            ]["example"]
            VersionResponse.model_validate(success)
            for invalid in ("", "x" * 65, "private/value"):
                with self.assertRaises(ValidationError):
                    VersionResponse.model_validate(success | {"version": invalid})


class ReadinessInterfaceTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_extra_exception_and_non_boolean_fail_closed(self):
        async def good():
            return True

        async def failure():
            raise RuntimeError("private-dsn-value")

        async def invalid():
            return "ready"

        for probes in (
            {},
            {"mongodb": good},
            dict.fromkeys(ReadinessGate.REQUIRED | {"extra"}, good),
            dict.fromkeys(ReadinessGate.REQUIRED, failure),
            dict.fromkeys(ReadinessGate.REQUIRED, invalid),
        ):
            self.assertFalse(await ReadinessGate(probes).ready())

    async def test_success_is_not_cached_and_recovers(self):
        available = True

        async def probe():
            return available

        gate = ReadinessGate(dict.fromkeys(ReadinessGate.REQUIRED, probe))
        self.assertTrue(await gate.ready())
        available = False
        self.assertFalse(await gate.ready())
        available = True
        self.assertTrue(await gate.ready())

    async def test_timeout_concurrency_cap_and_cancellation_cleanup(self):
        active = 0
        peak = 0

        async def slow():
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            try:
                await asyncio.sleep(10)
                return True
            finally:
                active -= 1

        gate = ReadinessGate(dict.fromkeys(ReadinessGate.REQUIRED, slow))
        start = time.monotonic()
        results = await asyncio.gather(*(gate.ready() for _ in range(20)))
        self.assertFalse(any(results))
        self.assertLess(time.monotonic() - start, 3)
        self.assertEqual(peak, 12)
        self.assertEqual(active, 0)
        pending = asyncio.create_task(gate.ready())
        await asyncio.sleep(0.01)
        pending.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await pending
        self.assertEqual(active, 0)
