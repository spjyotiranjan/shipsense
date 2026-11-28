"""Append one authentication receipt to a provisioned MongoDB collection identity."""

from uuid import UUID

from bson.binary import Binary
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from shipsense_api.session_storage_codec import AUDIT_COLLECTION


class MongoAuthReceiptAppend:
    """The expected UUID comes from separately verified deployment metadata."""

    def __init__(self, database: AsyncDatabase[dict[str, object]], collection_id: UUID) -> None:
        self._database = database
        self._collection_id = Binary.from_uuid(collection_id)

    async def __call__(self, transaction: AsyncClientSession, receipt: dict[str, object]) -> bool:
        if not transaction.in_transaction or transaction.client is not self._database.client:
            return False
        # UUID matching prevents an insert into a missing or replaced namespace.
        result = await self._database.client.admin.command(
            {
                "bulkWrite": 1,
                "nsInfo": [
                    {
                        "ns": f"{self._database.name}.{AUDIT_COLLECTION}",
                        "collectionUUID": self._collection_id,
                    }
                ],
                "ops": [{"insert": 0, "document": receipt}],
            },
            session=transaction,
        )
        cursor = result.get("cursor")
        if (
            result.get("ok") != 1
            or result.get("nErrors") != 0
            or result.get("nInserted") != 1
            or "writeConcernError" in result
            or not isinstance(cursor, dict)
            or cursor.get("id") != 0
        ):
            return False
        batch = cursor.get("firstBatch")
        if not isinstance(batch, list) or len(batch) != 1 or not isinstance(batch[0], dict):
            return False
        entry = batch[0]
        return entry.get("ok") == 1 and entry.get("idx") == 0 and entry.get("n") == 1
