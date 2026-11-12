"""Transactional write contract; deliberately no in-memory production fallback."""

from typing import Protocol
from uuid import UUID

from shipsense_domain.authorization import Decision, PrincipalContext
from shipsense_domain.models import IdentityContract


class IdentityUnitOfWork(Protocol):
    """One fenced transaction, with bounded retries and compare-and-set revisions.

    Implementations must re-resolve current caller/delegable authority and all
    ancestry; validate_identity/validate_transition alone do not authorize writes.
    Commit state, authz epoch, idempotency result and append-only audit together.
    Same key/different digest conflicts; retries recheck current authority before
    releasing a stored response. Failure rolls back all state. No adapter exists
    until authorized MongoDB write/index/transaction proof is available.
    """

    def commit(
        self,
        caller: PrincipalContext,
        expected_revision: int,
        replacement: IdentityContract,
        idempotency_key: UUID,
        request_digest: str,
        decision: Decision,
    ) -> None: ...
