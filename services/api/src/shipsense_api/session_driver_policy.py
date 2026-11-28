"""Isolated PyMongo policy candidate for the Decision 0012 session adapter."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import PyMongoError
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import ReadPreference
from pymongo.write_concern import WriteConcern

from shipsense_api.session_audit_append import MongoAuthReceiptAppend
from shipsense_api.session_storage_transactions import CommitOutcome


class PinnedSessionDriverPolicy:
    """Use only a dedicated client and independently verified collection metadata.

    Ambient PyMongo client-side timeout scopes are incompatible with the
    bounded retry policy. The adapter applies asyncio deadlines instead.
    """

    def __init__(self, database: AsyncDatabase[dict[str, object]], audit_id: UUID) -> None:
        self._client = database.client
        options = self._client.options
        if (
            options.timeout is not None
            or options.retry_reads
            or options.retry_writes
            or options.max_adaptive_retries != 0
        ):
            raise ValueError("Unsafe session database client options.")
        self.append_receipt = MongoAuthReceiptAppend(database, audit_id)

    @asynccontextmanager
    async def open(
        self, *, deadline: float, cleanup_limit: float
    ) -> AsyncIterator[AsyncClientSession]:
        if deadline <= asyncio.get_running_loop().time():
            raise TimeoutError()
        session = self._client.start_session()
        try:
            async with asyncio.timeout_at(deadline):
                await session.start_transaction(
                    read_preference=ReadPreference.PRIMARY,
                    read_concern=ReadConcern("snapshot"),
                    write_concern=WriteConcern("majority"),
                )
            yield session
        finally:
            async with asyncio.timeout(cleanup_limit):
                await session.end_session()

    async def commit(
        self, transaction: AsyncClientSession, *, deadline: float, send_limit: float
    ) -> CommitOutcome:
        if transaction.client is not self._client or not transaction.in_transaction:
            return CommitOutcome.UNKNOWN
        loop = asyncio.get_running_loop()
        end = min(deadline, loop.time() + send_limit)
        if loop.time() >= end:
            return CommitOutcome.UNKNOWN
        try:
            # This covers the entire single driver call including any implicit
            # repeat send. An unknown result never triggers another client call.
            async with asyncio.timeout_at(end):
                await transaction.commit_transaction()
        except PyMongoError, TimeoutError:
            return CommitOutcome.UNKNOWN
        if loop.time() >= end:
            return CommitOutcome.UNKNOWN
        return CommitOutcome.CONFIRMED_COMMIT
