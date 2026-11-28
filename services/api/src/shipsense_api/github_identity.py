"""Read canonical GitHub identity and email evidence from fixed HTTPS endpoints."""

import asyncio
import json
import re

import httpx
from shipsense_domain.provider_mailbox import ProviderMailbox, github_mailbox

from shipsense_api.service_credentials import InvalidServiceCredential, unique_object

_MAX_BODY_BYTES = 65_536
_EMAIL_PAGE_SIZE = 100
_MAX_EMAIL_PAGES = 5
_TOTAL_TIMEOUT = 5


class _InvalidGitHubResponse(ValueError):
    pass


async def _get_json(
    client: httpx.AsyncClient, path: str, *, params: dict[str, int] | None = None
) -> object:
    async with client.stream("GET", path, params=params) as response:
        if response.status_code != 200 or response.headers.get("content-encoding", "identity") != (
            "identity"
        ):
            raise _InvalidGitHubResponse()
        body = bytearray()
        async for chunk in response.aiter_bytes():
            if len(body) + len(chunk) > _MAX_BODY_BYTES:
                raise _InvalidGitHubResponse()
            body.extend(chunk)
    return json.loads(body, object_pairs_hook=unique_object)


async def verify_github_access_token(
    access_token: str, *, transport: httpx.AsyncBaseTransport | None = None
) -> ProviderMailbox | None:
    """Consume only an access token from a purpose-bound, validated OAuth exchange."""
    if not re.fullmatch(r"[A-Za-z0-9_.~+/\-]{1,512}=*", access_token) or len(access_token) > 512:
        return None
    try:
        async with (
            asyncio.timeout(_TOTAL_TIMEOUT),
            httpx.AsyncClient(
                base_url="https://api.github.com",
                follow_redirects=False,
                trust_env=False,
                timeout=_TOTAL_TIMEOUT,
                transport=transport,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Accept-Encoding": "identity",
                    "Authorization": f"Bearer {access_token}",
                    "User-Agent": "ShipSense",
                    "X-GitHub-Api-Version": "2026-03-10",
                },
            ) as client,
        ):
            profile = await _get_json(client, "/user")
            if not isinstance(profile, dict):
                return None
            emails: list[object] = []
            for page in range(1, _MAX_EMAIL_PAGES + 1):
                batch = await _get_json(
                    client, "/user/emails", params={"per_page": _EMAIL_PAGE_SIZE, "page": page}
                )
                if not isinstance(batch, list) or len(batch) > _EMAIL_PAGE_SIZE:
                    return None
                # Request only fixed paths. An empty page marks completion;
                # never follow a URL from a provider response.
                if not batch:
                    return github_mailbox(profile, emails)
                emails.extend(batch)
    except (
        httpx.HTTPError,
        TimeoutError,
        InvalidServiceCredential,
        ValueError,
        RecursionError,
    ):
        return None
    return None
