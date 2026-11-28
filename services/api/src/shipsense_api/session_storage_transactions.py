"""Decision 0012 orchestration with an explicit, unwired driver-policy seam."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from enum import Enum, auto
from typing import Protocol

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase
from shipsense_domain.sessions import SessionTransaction

from shipsense_api.session_storage_body import MongoSessionBody, StorageBodyFailed

_OPERATION_LIMIT = 2.0
_SEND_LIMIT = 0.5
_CLEANUP_LIMIT = 0.25


class CommitOutcome(Enum):
    CONFIRMED_COMMIT = auto()
    CONFIRMED_ABORT = auto()
    UNKNOWN = auto()


class StorageCommitNotConfirmed(StorageBodyFailed):
    def __init__(self, outcome: CommitOutcome) -> None:
        super().__init__()
        self.outcome = outcome


class MongoSessionPolicy(Protocol):
    """Trusted composition only. There is no default runtime policy.

    Budget parameters use the running loop's monotonic clock and seconds.
    A future reviewed policy must enforce these budgets at the driver boundary.
    """

    def open(
        self, *, deadline: float, cleanup_limit: float
    ) -> AbstractAsyncContextManager[AsyncClientSession]:
        """Yield one primary/snapshot/majority transaction on the expected client.

        Refuse missing or conflicting collections and prevent implicit audit
        collection creation, including concurrent namespace changes. Own
        partial-open cleanup and close on every path, without committing or
        suppressing the caller's exception. After commit begins, cleanup must
        not treat an ambiguous outcome as rollback.
        """
        ...

    async def append_receipt(
        self, transaction: AsyncClientSession, document: dict[str, object]
    ) -> bool:
        """Append to the verified audit collection in the same transaction.

        Return True only on acknowledgement. Prevent implicit creation or writes
        to a replacement namespace even if the collection changes after open.
        """
        ...

    async def commit(
        self, transaction: AsyncClientSession, *, deadline: float, send_limit: float
    ) -> CommitOutcome:
        """Own all commit sends. Report confirmation only on definitive evidence.

        Retry only an unknown result on this same transaction, at most once in
        total including implicit driver retries. Honor both remaining operation
        budget and per-send limit. Never replay the transaction body.
        """
        ...


class MongoSessionTransactions:
    def __init__(
        self, database: AsyncDatabase[dict[str, object]], policy: MongoSessionPolicy | None = None
    ) -> None:
        self._database = database
        self._policy = policy

    @asynccontextmanager
    async def begin(self) -> AsyncIterator[SessionTransaction]:
        policy = self._policy
        if policy is None:
            raise StorageBodyFailed()
        loop = asyncio.get_running_loop()
        deadline = loop.time() + _OPERATION_LIMIT
        task = asyncio.current_task()

        def remaining_budget() -> float:
            if task is not None and task.cancelling():
                raise asyncio.CancelledError()
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError()
            return remaining

        confirmed = False
        # Put cleanup outside the operation timeout; the policy owns bounded driver cleanup.
        async with AsyncExitStack() as cleanup:
            async with asyncio.timeout_at(deadline):
                transaction = await cleanup.enter_async_context(
                    policy.open(deadline=deadline, cleanup_limit=_CLEANUP_LIMIT)
                )
                remaining_budget()
                body = MongoSessionBody(self._database, transaction, policy.append_receipt)
                yield body
                body.require_receipt()
                outcome = await policy.commit(
                    transaction,
                    deadline=deadline,
                    send_limit=min(_SEND_LIMIT, remaining_budget()),
                )
                if outcome is not CommitOutcome.CONFIRMED_COMMIT:
                    raise StorageCommitNotConfirmed(outcome)
                remaining_budget()
                confirmed = True
        remaining_budget()
        if not confirmed:
            raise StorageBodyFailed()
