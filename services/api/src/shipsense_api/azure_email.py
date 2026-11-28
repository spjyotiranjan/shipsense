"""Submit one previously authorized auth email to Azure Communication Services."""

import asyncio
import base64
import binascii
import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field
from email.utils import formatdate
from typing import Literal
from uuid import UUID

import httpx

_SEND_PATH = "/emails:send?api-version=2025-09-01"
_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class EmailSubmission:
    outcome: Literal["accepted", "throttled", "rejected", "unknown"]
    attempt_id: UUID
    retry_after_seconds: int | None = None


def _mailbox(value: str) -> bool:
    return (
        len(value) <= 254
        and re.fullmatch(r"[^@\s\x00-\x1f\x7f]+@[^@\s\x00-\x1f\x7f]+", value) is not None
    )


@dataclass(frozen=True)
class AzureEmail:
    endpoint: str
    sender: str
    _key: bytes = field(repr=False)

    @classmethod
    def from_connection_string(cls, connection_string: str, sender: str) -> "AzureEmail":
        parts = {}
        for item in connection_string.strip().rstrip(";").split(";"):
            name, separator, value = item.partition("=")
            name = name.strip().lower()
            if not separator or name in parts:
                raise ValueError("Invalid Azure Email configuration.")
            parts[name] = value.strip()
        endpoint = parts.get("endpoint", "").rstrip("/").lower()
        if (
            set(parts) != {"endpoint", "accesskey"}
            or not re.fullmatch(r"https://(?:[a-z0-9-]+\.)+communications?\.azure\.com", endpoint)
            or not _mailbox(sender)
        ):
            raise ValueError("Invalid Azure Email configuration.")
        try:
            key = base64.b64decode(parts["accesskey"], validate=True)
        except ValueError, binascii.Error:
            raise ValueError("Invalid Azure Email configuration.") from None
        if not key:
            raise ValueError("Invalid Azure Email configuration.")
        return cls(endpoint, sender, key)

    async def submit(
        self,
        *,
        attempt_id: UUID,
        recipient: str,
        subject: str,
        body: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> EmailSubmission:
        """Return provider admission only. Leave retries to the durable caller."""
        if (
            not _mailbox(recipient)
            or not 1 <= len(subject) <= 120
            or not subject.isprintable()
            or not 1 <= len(body) <= 8192
        ):
            raise ValueError("Invalid authentication email.")
        content = json.dumps(
            {
                "senderAddress": self.sender,
                "recipients": {"to": [{"address": recipient}]},
                "content": {"subject": subject, "plainText": body},
                "userEngagementTrackingDisabled": True,
            },
            separators=(",", ":"),
        ).encode("ascii")
        timestamp = formatdate(usegmt=True)
        digest = base64.b64encode(hashlib.sha256(content).digest()).decode("ascii")
        host = self.endpoint.removeprefix("https://")
        signed = f"POST\n{_SEND_PATH}\n{timestamp};{host};{digest}".encode("ascii")
        signature = base64.b64encode(hmac.digest(self._key, signed, "sha256")).decode("ascii")
        headers = {
            "Content-Type": "application/json",
            "x-ms-date": timestamp,
            "x-ms-content-sha256": digest,
            "Authorization": (
                "HMAC-SHA256 SignedHeaders=x-ms-date;host;x-ms-content-sha256&Signature="
                + signature
            ),
            "Operation-Id": str(attempt_id),
        }
        try:
            async with (
                asyncio.timeout(_TIMEOUT_SECONDS),
                httpx.AsyncClient(
                    follow_redirects=False, trust_env=False, transport=transport
                ) as client,
                client.stream(
                    "POST", self.endpoint + _SEND_PATH, content=content, headers=headers
                ) as response,
            ):
                status = response.status_code
                if status == 202:
                    return EmailSubmission("accepted", attempt_id)
                if status == 429:
                    delay = response.headers.get("retry-after", "")
                    seconds = int(delay) if re.fullmatch(r"[0-9]{1,5}", delay) else None
                    return EmailSubmission("throttled", attempt_id, seconds)
                if 400 <= status < 500 and status != 408:
                    return EmailSubmission("rejected", attempt_id)
        except httpx.HTTPError, TimeoutError:
            pass
        return EmailSubmission("unknown", attempt_id)
