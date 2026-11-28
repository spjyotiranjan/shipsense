import base64
import hashlib
import hmac
import json
import unittest
from uuid import UUID

import httpx
from shipsense_api.azure_email import AzureEmail, EmailSubmission

ATTEMPT = UUID(int=10)
KEY = b"fixture-key-for-local-signature-test"
ENDPOINT = "https://fixture.communication.azure.com"
SENDER = "test@sender.example"


class AzureEmailTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        key = base64.b64encode(KEY).decode("ascii")
        self.mail = AzureEmail.from_connection_string(
            f"endpoint={ENDPOINT};accesskey={key}", SENDER
        )

    async def submit(self, respond):
        return await self.mail.submit(
            attempt_id=ATTEMPT,
            recipient="person@example.invalid",
            subject="Verify your email",
            body="Open the verification link.",
            transport=httpx.MockTransport(respond),
        )

    async def test_signs_exact_body_and_reports_admission(self):
        def respond(request):
            self.assertEqual(request.method, "POST")
            self.assertEqual(str(request.url), ENDPOINT + "/emails:send?api-version=2025-09-01")
            self.assertEqual(request.headers["operation-id"], str(ATTEMPT))
            self.assertEqual(
                json.loads(request.content),
                {
                    "senderAddress": SENDER,
                    "recipients": {"to": [{"address": "person@example.invalid"}]},
                    "content": {
                        "subject": "Verify your email",
                        "plainText": "Open the verification link.",
                    },
                    "userEngagementTrackingDisabled": True,
                },
            )
            content_hash = base64.b64encode(hashlib.sha256(request.content).digest()).decode()
            self.assertEqual(request.headers["x-ms-content-sha256"], content_hash)
            canonical = (
                f"POST\n{request.url.raw_path.decode()}\n{request.headers['x-ms-date']};"
                f"{request.url.host};{content_hash}"
            )
            expected = base64.b64encode(hmac.digest(KEY, canonical.encode(), "sha256")).decode()
            self.assertTrue(request.headers["authorization"].endswith("&Signature=" + expected))
            return httpx.Response(202)

        self.assertEqual(await self.submit(respond), EmailSubmission("accepted", ATTEMPT))

    async def test_outage_throttle_and_redirect_do_not_retry(self):
        for status, outcome, seconds in (
            (429, "throttled", 60),
            (403, "rejected", None),
            (408, "unknown", None),
            (503, "unknown", None),
            (307, "unknown", None),
        ):
            with self.subTest(status=status):
                calls = []

                def respond(request):
                    calls.append(request.url.host)
                    return httpx.Response(
                        status,
                        headers={"retry-after": "60", "location": "https://other.example"},
                    )

                self.assertEqual(
                    await self.submit(respond), EmailSubmission(outcome, ATTEMPT, seconds)
                )
                self.assertEqual(calls, ["fixture.communication.azure.com"])

    async def test_lost_response_is_unknown(self):
        def respond(request):
            raise httpx.ReadTimeout("synthetic timeout", request=request)

        self.assertEqual(await self.submit(respond), EmailSubmission("unknown", ATTEMPT))

    def test_configuration_rejects_foreign_hosts_and_malformed_keys(self):
        for value in (
            "endpoint=https://example.invalid;accesskey=YQ==",
            f"endpoint={ENDPOINT}/send;accesskey=YQ==",
            f"endpoint={ENDPOINT};accesskey=invalid!",
        ):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(ValueError, "^Invalid Azure Email configuration[.]$"),
            ):
                AzureEmail.from_connection_string(value, SENDER)
