"""Canonical session rules and fenced atomic port; no runtime storage adapter."""

import hashlib
import re
from contextlib import AbstractAsyncContextManager
from typing import Annotated, Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

Counter = Annotated[StrictInt, Field(ge=1)]
Instant = Annotated[StrictInt, Field(ge=0)]


class SessionDenied(Exception):
    """No distinction between absent, inactive, revoked or expired authority."""


class SessionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    handle_digest: str = Field(pattern=r"^[a-f0-9]{64}$", repr=False)
    account_id: UUID
    authentication_epoch: Counter
    created_at: Instant
    last_activity_at: Instant
    absolute_expires_at: Instant
    idle_expires_at: Instant
    revoked_at: Instant | None = None
    revision: Counter

    @model_validator(mode="after")
    def bounds(self) -> SessionRecord:
        if not (
            self.created_at
            <= self.last_activity_at
            < self.absolute_expires_at
            <= self.created_at + 900
            and self.last_activity_at < self.idle_expires_at <= self.last_activity_at + 600
            and (self.revoked_at is None or self.revoked_at >= self.created_at)
        ):
            raise ValueError("Invalid session bounds.")
        return self


class SessionAccount(BaseModel):
    """Authentication state only; grants no tenant membership or permission."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    account_id: UUID
    authentication_epoch: Counter
    status: Literal["active", "suspended", "archived"]
    revision: Counter


class SessionAudit(BaseModel):
    """Unscoped authentication partition; contains no credential or object lookup ID.

    Not a tenant audit timeline entry. Event IDs are unique per attempt; request
    correlation is trace context, never authority or an idempotency key.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    event_id: UUID
    partition: Literal["authentication"] = "authentication"
    actor: Literal["shipsense-bff"] = "shipsense-bff"
    action: Literal["session.resolve", "session.revoke"]
    outcome: Literal["allowed", "denied", "revoked"]
    recorded_at: Instant
    correlation_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")


def handle_digest(handle: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", handle):
        raise SessionDenied()
    return hashlib.sha256(handle.encode("ascii")).hexdigest()


def resolve_session(
    record: SessionRecord | None, account: SessionAccount | None, now: int
) -> SessionRecord:
    if (
        record is None
        or account is None
        or account.account_id != record.account_id
        or account.status != "active"
        or account.authentication_epoch != record.authentication_epoch
        or record.revoked_at is not None
        or not record.last_activity_at
        <= now
        < min(record.absolute_expires_at, record.idle_expires_at)
    ):
        raise SessionDenied()
    return record


def revoke_session(record: SessionRecord, now: int) -> SessionRecord:
    if now < record.last_activity_at:
        raise SessionDenied()
    if record.revoked_at is not None:
        return record
    return SessionRecord.model_validate(
        {**record.model_dump(), "revoked_at": now, "revision": record.revision + 1}
    )


class SessionTransaction(Protocol):
    async def session(self, digest: str) -> SessionRecord | None: ...

    async def account(self, account_id: UUID) -> SessionAccount | None: ...

    async def replace(self, expected: SessionRecord, replacement: SessionRecord) -> None:
        """CAS revision; preserve identity/epoch/times, change only revoke/revision."""
        ...

    async def append(self, event: SessionAudit) -> None: ...


class SessionTransactions(Protocol):
    def begin(self) -> AbstractAsyncContextManager[SessionTransaction]:
        """Fence session AND account epoch/state until atomic commit on clean exit.

        Every resolve (including denial) appends its receipt before returning.
        All replacements and audit commit together or roll back; commit failure
        must raise. Bound retries/deadlines, recheck authority/time on retry, and
        never replay a successful resolve after a fence conflict. Account changes
        must contend on the same fence. No adapter or durability claim exists yet.
        """
        ...
