"""Decision 0012's unwired MongoDB transaction body, without lifecycle or commit policy."""

import re
from collections.abc import Awaitable, Callable, Mapping
from uuid import UUID

from bson import Int64
from pymongo import ReturnDocument
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from shipsense_domain.sessions import SessionAccount, SessionAudit, SessionRecord, revoke_session

from shipsense_api.session_storage_codec import (
    ACCOUNT_COLLECTION,
    MAX_INT64,
    SESSION_COLLECTION,
    InvalidStorageRecord,
    decode_account,
    decode_session,
    encode_audit,
)


class StorageBodyFailed(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Session transaction body failed.")


class MongoSessionBody:
    """Use once, sequentially, inside a verified caller-owned transaction.

    The caller must discard the body and abort on a failed or cancelled operation.
    This object never starts or commits a transaction and cannot release authority.
    """

    def __init__(
        self,
        database: AsyncDatabase[dict[str, object]],
        transaction: AsyncClientSession,
        append_receipt: Callable[[AsyncClientSession, dict[str, object]], Awaitable[bool]]
        | None = None,
    ) -> None:
        self._database = database
        self._transaction = transaction
        self._append_receipt = append_receipt
        self._ready = True
        self._session_checked = False
        self._account_checked = False
        self._record: SessionRecord | None = None
        self._account: SessionAccount | None = None
        self._session_fence: Int64 | None = None
        self._replacement: SessionRecord | None = None
        self._receipt = False

    def _enter(self) -> None:
        if (
            not self._ready
            or not self._transaction.in_transaction
            or self._transaction.client is not self._database.client
        ):
            raise StorageBodyFailed()
        self._ready = False  # Leave unusable on any failure/cancellation.

    async def _fence(
        self, collection: AsyncCollection[dict[str, object]], key: str
    ) -> Mapping[str, object] | None:
        document = await collection.find_one_and_update(
            {"_id": key},
            {"$inc": {"fence": Int64(1)}},
            upsert=False,
            return_document=ReturnDocument.BEFORE,
            collation={"locale": "simple"},
            session=self._transaction,
        )
        # Decode the preimage so an increment cannot normalize a malformed fence.
        if document is not None:
            fence = document.get("fence")
            if not isinstance(fence, Int64) or not 1 <= fence < MAX_INT64:
                raise StorageBodyFailed()
        return document

    async def session(self, digest: str) -> SessionRecord | None:
        self._enter()
        if self._session_checked or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise StorageBodyFailed()
        row = await self._fence(self._database[SESSION_COLLECTION], digest)
        if row is not None:
            try:
                self._record = decode_session(row, digest)
            except InvalidStorageRecord:
                raise StorageBodyFailed() from None
            fence = row["fence"]
            assert isinstance(fence, Int64)  # Already validated by the fence and codec.
            self._session_fence = Int64(fence + 1)
        self._session_checked = self._ready = True
        return self._record

    async def account(self, account_id: UUID) -> SessionAccount | None:
        self._enter()
        if self._account_checked or self._record is None or account_id != self._record.account_id:
            raise StorageBodyFailed()
        row = await self._fence(self._database[ACCOUNT_COLLECTION], str(account_id))
        if row is not None:
            try:
                self._account = decode_account(row, account_id)
            except InvalidStorageRecord:
                raise StorageBodyFailed() from None
        self._account_checked = self._ready = True
        return self._account

    async def replace(self, expected: SessionRecord, replacement: SessionRecord) -> None:
        self._enter()
        revoked_at = replacement.revoked_at
        if (
            self._replacement is not None
            or self._account is None
            or expected != self._record
            or expected.revoked_at is not None
            or expected.revision >= MAX_INT64
            or revoked_at is None
            or not expected.last_activity_at <= revoked_at <= MAX_INT64
            or replacement != revoke_session(expected, revoked_at)
        ):
            raise StorageBodyFailed()
        result = await self._database[SESSION_COLLECTION].update_one(
            {
                "_id": expected.handle_digest,
                "schema_version": 1,
                "fence": self._session_fence,
                "revision": Int64(expected.revision),
                "revoked_at": None,
            },
            {"$set": {"revision": Int64(replacement.revision), "revoked_at": Int64(revoked_at)}},
            upsert=False,
            collation={"locale": "simple"},
            session=self._transaction,
        )
        if not result.acknowledged or result.matched_count != 1:
            raise StorageBodyFailed()
        self._replacement = replacement
        self._ready = True

    async def append(self, event: SessionAudit) -> None:
        self._enter()
        if not self._session_checked or (self._record is not None and not self._account_checked):
            raise StorageBodyFailed()
        if event.action == "session.revoke":
            if event.outcome != "revoked" or (
                self._record is not None
                and (
                    self._account is None
                    or (self._record.revoked_at is None and self._replacement is None)
                    or (
                        self._replacement is not None
                        and self._replacement.revoked_at != event.recorded_at
                    )
                )
            ):
                raise StorageBodyFailed()
        elif self._replacement is not None or event.outcome not in {"allowed", "denied"}:
            raise StorageBodyFailed()
        # A raw insert can implicitly create a missing collection. Require a
        # deployment policy with an acknowledged, same-transaction append instead.
        if self._append_receipt is None:
            raise StorageBodyFailed()
        if await self._append_receipt(self._transaction, encode_audit(event)) is not True:
            raise StorageBodyFailed()
        self._receipt = True  # The one-receipt body is closed to further writes.

    def require_receipt(self) -> None:
        if not self._receipt or not self._transaction.in_transaction:
            raise StorageBodyFailed()
