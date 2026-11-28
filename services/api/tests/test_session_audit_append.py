import unittest
from unittest.mock import AsyncMock, Mock
from uuid import UUID

from bson.binary import Binary
from pymongo.errors import OperationFailure
from shipsense_api.session_audit_append import MongoAuthReceiptAppend

COLLECTION_ID = UUID(int=1)
RECEIPT = {"test": "synthetic"}
ACCEPTED = {
    "ok": 1.0,
    "nErrors": 0,
    "nInserted": 1,
    "cursor": {"id": 0, "firstBatch": [{"ok": 1.0, "idx": 0, "n": 1}]},
}


class MongoAuthReceiptTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = Mock()
        self.client.admin.command = AsyncMock(return_value=ACCEPTED)
        self.database = Mock(client=self.client)
        self.database.name = "synthetic_auth"
        self.transaction = Mock(in_transaction=True, client=self.client)
        self.append = MongoAuthReceiptAppend(self.database, COLLECTION_ID)

    async def test_append_binds_uuid_and_transaction(self):
        self.assertTrue(await self.append(self.transaction, RECEIPT))
        self.client.admin.command.assert_awaited_once_with(
            {
                "bulkWrite": 1,
                "nsInfo": [
                    {
                        "ns": "synthetic_auth.auth_session_audit",
                        "collectionUUID": Binary.from_uuid(COLLECTION_ID),
                    }
                ],
                "ops": [{"insert": 0, "document": RECEIPT}],
            },
            session=self.transaction,
        )

    async def test_invalid_transaction_does_not_send(self):
        self.assertFalse(await self.append(Mock(in_transaction=False, client=self.client), RECEIPT))
        self.assertFalse(await self.append(Mock(in_transaction=True, client=Mock()), RECEIPT))
        self.client.admin.command.assert_not_awaited()

    async def test_write_error_and_incomplete_receipt_cannot_succeed(self):
        for response in (
            {"ok": 1, "nInserted": 1},
            ACCEPTED | {"nErrors": 1},
            ACCEPTED | {"writeConcernError": {"code": 64}},
            ACCEPTED | {"cursor": {"id": 1, "firstBatch": []}},
            ACCEPTED | {"cursor": {"id": 0, "firstBatch": [{"ok": 0, "code": 361}]}},
        ):
            with self.subTest(response=response):
                self.client.admin.command.return_value = response
                self.assertFalse(await self.append(self.transaction, RECEIPT))

        self.client.admin.command.side_effect = OperationFailure("collection UUID mismatch", 361)
        with self.assertRaises(OperationFailure):
            await self.append(self.transaction, RECEIPT)
