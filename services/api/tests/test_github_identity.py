import unittest

import httpx
from shipsense_api.github_identity import verify_github_access_token
from shipsense_domain.account_matching import ProviderSubject
from shipsense_domain.provider_mailbox import ProviderMailbox

TOKEN = "synthetic-exchange-token"
PRIMARY = {"email": "person@example.invalid", "primary": True, "verified": True}
SECONDARY = {"email": "alternate@example.invalid", "primary": False, "verified": True}


class GitHubIdentityTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.requests = []

    def respond(self, request, pages):
        self.requests.append(request)
        self.assertEqual(request.url.host, "api.github.com")
        self.assertEqual(request.headers["authorization"], f"Bearer {TOKEN}")
        if request.url.path == "/user":
            return httpx.Response(
                200, json={"id": 42, "login": "renameable", "email": "profile@example.invalid"}
            )
        self.assertEqual(request.url.path, "/user/emails")
        self.assertEqual(request.url.params.get("per_page"), "100")
        return pages[int(request.url.params["page"]) - 1]

    async def verify(self, pages):
        return await verify_github_access_token(
            TOKEN, transport=httpx.MockTransport(lambda request: self.respond(request, pages))
        )

    async def test_fetches_all_pages_using_fixed_paths_and_prefers_private_primary(self):
        result = await self.verify(
            [
                httpx.Response(
                    200, json=[SECONDARY], headers={"Link": "<https://example.invalid>"}
                ),
                httpx.Response(200, json=[PRIMARY]),
                httpx.Response(200, json=[]),
            ]
        )
        self.assertEqual(
            result, ProviderMailbox(ProviderSubject("github", "42"), "person@example.invalid")
        )
        self.assertEqual(len(self.requests), 4)

    async def test_does_not_accept_partial_credentials_after_error_or_redirect(self):
        for invalid in (
            httpx.Response(403),
            httpx.Response(302, headers={"Location": "https://example.invalid"}),
            httpx.Response(200, content=b"[" + b" " * 65536 + b"]"),
        ):
            with self.subTest(invalid=invalid.status_code):
                self.requests.clear()
                self.assertIsNone(await self.verify([httpx.Response(200, json=[PRIMARY]), invalid]))
                self.assertEqual(len(self.requests), 3)

    async def test_page_budget_exhaustion_denies_even_after_primary_seen(self):
        self.assertIsNone(await self.verify([httpx.Response(200, json=[PRIMARY])] * 5))
        self.assertEqual(len(self.requests), 6)
