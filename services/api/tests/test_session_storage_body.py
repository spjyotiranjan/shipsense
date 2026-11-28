import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from bson import BSON, Int64
from shipsense_api.session_storage_body import MongoSessionBody, StorageBodyFailed
from shipsense_api.session_storage_codec import (
    ACCOUNT_COLLECTION,
    MAX_INT64,
    SESSION_COLLECTION,
)
from shipsense_domain.sessions import SessionAudit, revoke_session

_ACCOUNT = UUID(int=2)
_DIGEST = "a" * 64


class StorageFixture:
    def setUp(self):
        self.db = MagicMock()
        self.tx = MagicMock(client=self.db.client, in_transaction=True)
        self.sessions = MagicMock(find_one_and_update=AsyncMock(), update_one=AsyncMock())
        self.accounts = MagicMock(find_one_and_update=AsyncMock())
        self.append_receipt = AsyncMock(return_value=True)
        self.db.__getitem__.side_effect = {
            SESSION_COLLECTION: self.sessions,
            ACCOUNT_COLLECTION: self.accounts,
        }.__getitem__
        self.sessions.find_one_and_update.return_value = BSON.encode(
            dict(
                _id=_DIGEST,
                schema_version=1,
                fence=Int64(11),
                account_id=str(_ACCOUNT),
                authentication_epoch=Int64(2),
                created_at=Int64(1000),
                last_activity_at=Int64(1100),
                absolute_expires_at=Int64(1900),
                idle_expires_at=Int64(1700),
                revoked_at=None,
                revision=Int64(3),
            )
        ).decode()
        self.accounts.find_one_and_update.return_value = BSON.encode(
            dict(
                _id=str(_ACCOUNT),
                schema_version=1,
                fence=Int64(17),
                authentication_epoch=Int64(2),
                revision=Int64(4),
                status="active",
            )
        ).decode()
        self.sessions.update_one.return_value = MagicMock(acknowledged=True, matched_count=1)

        self.receipt = SessionAudit(
            event_id=UUID(int=3),
            action="session.revoke",
            outcome="revoked",
            recorded_at=1200,
            correlation_id="00000000-0000-4000-8000-000000000003",
        )


class StorageBodyTests(StorageFixture, unittest.IsolatedAsyncioTestCase):
    async def test_body_fences_preimages_and_revokes_with_same_transaction_receipt(self):
        body = MongoSessionBody(self.db, self.tx, self.append_receipt)
        record = await body.session(_DIGEST)
        self.accounts.find_one_and_update.assert_not_awaited()
        await body.account(record.account_id)
        await body.replace(record, revoke_session(record, 1200))
        await body.append(self.receipt)
        for collection, key in ((self.sessions, _DIGEST), (self.accounts, str(_ACCOUNT))):
            args, kwargs = collection.find_one_and_update.await_args
            self.assertEqual(args, ({"_id": key}, {"$inc": {"fence": Int64(1)}}))
            self.assertIs(type(args[1]["$inc"]["fence"]), Int64)
            self.assertIs(kwargs["session"], self.tx)
            self.assertFalse(kwargs["return_document"])
            self.assertFalse(kwargs["upsert"])
            self.assertEqual(kwargs["collation"], {"locale": "simple"})
        args, kwargs = self.sessions.update_one.await_args
        self.assertEqual(
            args,
            (
                {
                    "_id": _DIGEST,
                    "schema_version": 1,
                    "fence": Int64(12),
                    "revision": Int64(3),
                    "revoked_at": None,
                },
                {"$set": {"revision": Int64(4), "revoked_at": Int64(1200)}},
            ),
        )
        self.assertIs(kwargs["session"], self.tx)
        self.assertFalse(kwargs["upsert"])
        args, _ = self.append_receipt.await_args
        self.assertIs(args[0], self.tx)
        self.assertEqual(args[1]["_id"], str(self.receipt.event_id))
        self.assertEqual(args[1]["outcome"], "revoked")
        self.assertNotIn(_DIGEST, str(args[1]))
        self.tx.commit_transaction.assert_not_called()

    async def test_cas_miss_prevents_receipt(self):
        self.sessions.update_one.return_value.matched_count = 0
        body = MongoSessionBody(self.db, self.tx, self.append_receipt)
        record = await body.session(_DIGEST)
        await body.account(record.account_id)
        with self.assertRaises(StorageBodyFailed):
            await body.replace(record, revoke_session(record, 1200))
        with self.assertRaises(StorageBodyFailed):
            await body.append(self.receipt)
        self.append_receipt.assert_not_awaited()

    async def test_fence_refuses_wrong_account_and_malformed_preimage(self):
        for fence in (11, Int64(MAX_INT64)):
            with self.subTest(fence=fence):
                body = MongoSessionBody(self.db, self.tx)
                self.sessions.find_one_and_update.return_value["fence"] = fence
                with self.assertRaises(StorageBodyFailed):
                    await body.session(_DIGEST)
        self.sessions.find_one_and_update.return_value["fence"] = Int64(11)
        body = MongoSessionBody(self.db, self.tx)
        await body.session(_DIGEST)
        with self.assertRaises(StorageBodyFailed):
            await body.account(UUID(int=77))
        self.accounts.find_one_and_update.assert_not_awaited()

    async def test_inactive_or_wrong_client_does_not_issue_commands(self):
        for tx in (
            MagicMock(client=object(), in_transaction=True),
            MagicMock(client=self.db.client, in_transaction=False),
        ):
            with self.assertRaises(StorageBodyFailed):
                await MongoSessionBody(self.db, tx).session(_DIGEST)
        self.sessions.find_one_and_update.assert_not_awaited()

    async def test_absent_session_resolve_audits_denial_without_account_lookup(self):
        self.sessions.find_one_and_update.return_value = None
        body = MongoSessionBody(self.db, self.tx, self.append_receipt)
        self.assertIsNone(await body.session(_DIGEST))
        await body.append(
            self.receipt.model_copy(update={"action": "session.resolve", "outcome": "denied"})
        )
        self.accounts.find_one_and_update.assert_not_awaited()
        self.append_receipt.assert_awaited_once()
        body.require_receipt()

    async def test_no_raw_insert_can_implicitly_create_the_audit_collection(self):
        self.sessions.find_one_and_update.return_value = None
        body = MongoSessionBody(self.db, self.tx)
        await body.session(_DIGEST)
        self.db.__getitem__.reset_mock()
        with self.assertRaises(StorageBodyFailed):
            await body.append(self.receipt)
        self.db.__getitem__.assert_not_called()

    async def test_allowed_receipt_requires_a_valid_fenced_observation(self):
        self.sessions.find_one_and_update.return_value = None
        body = MongoSessionBody(self.db, self.tx, self.append_receipt)
        await body.session(_DIGEST)
        with self.assertRaises(StorageBodyFailed):
            await body.append(
                self.receipt.model_copy(update={"action": "session.resolve", "outcome": "allowed"})
            )
        self.append_receipt.assert_not_awaited()

    async def test_second_append_invalidates_a_previously_staged_receipt(self):
        self.sessions.find_one_and_update.return_value = None
        body = MongoSessionBody(self.db, self.tx, self.append_receipt)
        await body.session(_DIGEST)
        await body.append(self.receipt)
        with self.assertRaises(StorageBodyFailed):
            await body.append(self.receipt)
        with self.assertRaises(StorageBodyFailed):
            body.require_receipt()

    async def test_missing_or_unacknowledged_receipt_cannot_seal_the_body(self):
        self.sessions.find_one_and_update.return_value = None
        self.append_receipt.return_value = False
        with self.assertRaises(StorageBodyFailed):
            MongoSessionBody(self.db, self.tx).require_receipt()
        body = MongoSessionBody(self.db, self.tx, self.append_receipt)
        await body.session(_DIGEST)
        with self.assertRaises(StorageBodyFailed):
            await body.append(self.receipt)
        self.append_receipt.assert_awaited_once()
        with self.assertRaises(StorageBodyFailed):
            body.require_receipt()
