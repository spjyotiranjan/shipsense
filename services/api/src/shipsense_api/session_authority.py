"""Composition for a future fenced store; intentionally absent from default app."""

import time
from collections.abc import Callable
from uuid import uuid4

from shipsense_domain.sessions import (
    SessionAudit,
    SessionDenied,
    SessionTransactions,
    handle_digest,
    resolve_session,
    revoke_session,
)

from shipsense_api.session_bridge import AuthorityUnavailable, SessionSnapshot


class CanonicalSessionAuthority:
    def __init__(
        self, transactions: SessionTransactions, clock: Callable[[], int] = lambda: int(time.time())
    ) -> None:
        self.transactions = transactions
        self.clock = clock

    async def resolve(self, handle: str, correlation_id: str) -> SessionSnapshot:
        digest = handle_digest(handle)
        snapshot = None
        try:
            async with self.transactions.begin() as tx:
                record = await tx.session(digest)
                account = await tx.account(record.account_id) if record is not None else None
                now = self.clock()
                try:
                    if record is not None and record.handle_digest != digest:
                        raise SessionDenied()
                    valid = resolve_session(record, account, now)
                    snapshot = SessionSnapshot(
                        createdAt=valid.created_at,
                        lastActivityAt=valid.last_activity_at,
                        absoluteExpiresAt=valid.absolute_expires_at,
                        idleExpiresAt=valid.idle_expires_at,
                    )
                    snapshot.check(now)
                except SessionDenied:
                    snapshot = None
                await tx.append(
                    SessionAudit(
                        event_id=uuid4(),
                        action="session.resolve",
                        outcome="allowed" if snapshot is not None else "denied",
                        recorded_at=now,
                        correlation_id=correlation_id,
                    )
                )
        except Exception:
            raise AuthorityUnavailable() from None
        if snapshot is None:
            raise SessionDenied()
        return snapshot

    async def revoke(self, handle: str, correlation_id: str) -> None:
        digest = handle_digest(handle)
        try:
            async with self.transactions.begin() as tx:
                record = await tx.session(digest)
                now = self.clock()
                if record is not None:
                    if record.handle_digest != digest:
                        raise SessionDenied()
                    replacement = revoke_session(record, now)
                    if replacement is not record:
                        await tx.replace(record, replacement)
                await tx.append(
                    SessionAudit(
                        event_id=uuid4(),
                        action="session.revoke",
                        outcome="revoked",
                        recorded_at=now,
                        correlation_id=correlation_id,
                    )
                )
        except Exception:
            raise AuthorityUnavailable() from None
