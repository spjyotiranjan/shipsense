"""Credential-free worker boundary for a fixed scoped read; never dispatches effects."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID

from shipsense_domain.authorization import HiddenResource, PrincipalContext, before_deadline
from shipsense_domain.models import Contract, ResourceScope
from shipsense_domain.scoped_queries import MetadataGateway

WORKER_AUDIENCE = "shipsense-worker"


class DelegatedCount(Contract):
    job_id: UUID
    delegation_id: UUID
    scope: ResourceScope


@dataclass(frozen=True)
class VerifiedWorker:
    """Trusted verifier output, never deserialized from the queue."""

    worker_id: UUID
    tenant_id: UUID
    audience: str
    expires_at: datetime


@dataclass(frozen=True)
class Delegation:
    job_id: UUID
    delegation_id: UUID
    worker_id: UUID
    scope: ResourceScope
    expires_at: datetime
    active: bool
    principal: PrincipalContext


class WorkerCountHarness:
    def __init__(
        self,
        verify: Callable[[str], VerifiedWorker | None],
        resolve: Callable[[UUID, UUID, UUID], Delegation | None],
        gateway: MetadataGateway,
        clock: Callable[[], datetime],
    ) -> None:
        self._verify = verify
        self._resolve = resolve
        self._gateway = gateway
        self._clock = clock

    def count(self, credential: str, request: DelegatedCount, correlation_id: UUID) -> int:
        worker = self._verify(credential)
        if (
            worker is None
            or worker.audience != WORKER_AUDIENCE
            or worker.tenant_id != request.scope.tenant_id
            or not before_deadline(self._clock(), worker.expires_at)
        ):
            raise HiddenResource()
        delegation = self._resolve(worker.tenant_id, request.job_id, request.delegation_id)
        now = self._clock()
        if (
            delegation is None
            or delegation.active is not True
            or delegation.worker_id != worker.worker_id
            or delegation.job_id != request.job_id
            or delegation.delegation_id != request.delegation_id
            or delegation.scope != request.scope
            or delegation.principal.tenant_id != worker.tenant_id
            or not before_deadline(now, delegation.expires_at)
            or not before_deadline(now, delegation.principal.expires_at)
            or not before_deadline(now, worker.expires_at)
        ):
            raise HiddenResource()
        context = replace(
            delegation.principal,
            expires_at=min(
                delegation.principal.expires_at.astimezone(UTC),
                delegation.expires_at.astimezone(UTC),
                worker.expires_at.astimezone(UTC),
            ),
        )
        count = self._gateway.count(context, delegation.scope, correlation_id)
        if not before_deadline(self._clock(), context.expires_at):
            raise HiddenResource()
        return count
