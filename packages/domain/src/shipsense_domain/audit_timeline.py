"""Exact-scope, bounded audit reconstruction; no database or archive adapter."""

from collections.abc import Callable
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from shipsense_domain.authorization import AuthorizationService, HiddenResource, PrincipalContext
from shipsense_domain.models import Contract, ResourceScope, Revision, Timestamp

MAX_CORRELATION_EVENTS = 100


class AuditRecord(Contract):
    event_id: UUID
    scope: ResourceScope
    correlation_id: UUID
    sequence: Revision
    recorded_at: Timestamp
    actor_id: UUID
    kind: Literal[
        "sensitive_read",
        "policy_decision",
        "proposal_recorded",
        "approval_assessed",
        "synthetic_attempt",
        "synthetic_receipt",
    ]
    reference_id: UUID


class AuditJournal(Protocol):
    """The adapter must scope the storage query before limit, with no fallback or global scan."""

    def correlation(
        self, scope: ResourceScope, correlation_id: UUID, limit: int
    ) -> tuple[AuditRecord, ...]: ...


class InvalidTimeline(Exception):
    def __init__(self) -> None:
        super().__init__("Audit timeline unavailable.")


class TimelineReader:
    def __init__(
        self, auth: AuthorizationService, journal: AuditJournal, clock: Callable[[], datetime]
    ) -> None:
        self._auth = auth
        self._journal = journal
        self._clock = clock

    def read(
        self,
        context: PrincipalContext,
        scope: ResourceScope,
        target_correlation_id: UUID,
        request_correlation_id: UUID,
    ) -> tuple[AuditRecord, ...]:
        decision = self._auth.evaluate(
            context, "audit.read", scope, self._clock(), request_correlation_id
        )
        if not decision.live_at(self._clock()):
            raise HiddenResource()
        # Request one extra to detect oversize rather than quietly return a truncated trace.
        records = self._journal.correlation(
            scope, target_correlation_id, MAX_CORRELATION_EVENTS + 1
        )
        # Never classify an expired request by the contents of the fetched stream.
        if not decision.live_at(self._clock()):
            raise HiddenResource()
        invalid = (
            len(records) > MAX_CORRELATION_EVENTS
            or any(
                event.scope != scope or event.correlation_id != target_correlation_id
                for event in records
            )
            or len({event.sequence for event in records}) != len(records)
            or len({event.event_id for event in records}) != len(records)
        )
        if invalid:
            if not decision.live_at(self._clock()):
                raise HiddenResource()
            raise InvalidTimeline()
        ordered = tuple(sorted(records, key=lambda event: event.sequence))
        if not decision.live_at(self._clock()):
            raise HiddenResource()
        return ordered
