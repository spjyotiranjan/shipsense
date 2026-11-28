"""Observe pinned PyMongo retry behavior over loopback; not a MongoDB implementation."""

import asyncio
import struct
import unittest
from contextlib import suppress

from bson import BSON
from pymongo import AsyncMongoClient
from pymongo.errors import ConnectionFailure
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

_HEADER = struct.Struct("<iiii")


class TransactionWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_pinned_driver_can_send_two_commits_despite_retry_writes_false(self):
        await self.check_commit_sends(unacknowledged=1, timeout_ms=None)

    async def test_client_side_operation_timeout_can_send_more_than_two_commits(self):
        await self.check_commit_sends(unacknowledged=2, timeout_ms=7000)

    async def test_without_client_side_timeout_two_lost_acks_stop_without_confirmation(self):
        await self.check_commit_sends(unacknowledged=2, timeout_ms=None, confirmed=False)

    async def check_commit_sends(
        self, *, unacknowledged: int, timeout_ms: int | None, confirmed: bool = True
    ) -> None:
        commits = []
        inserts = []
        sockets = set()
        handlers = set()
        failures = []

        async def respond(reader, writer):
            sockets.add(writer)
            task = asyncio.current_task()
            handlers.add(task)
            try:
                while True:
                    length, request_id, _, opcode = _HEADER.unpack(
                        await reader.readexactly(_HEADER.size)
                    )
                    if not _HEADER.size <= length <= 1_048_576:
                        raise AssertionError("Unexpected message size")
                    body = await reader.readexactly(length - _HEADER.size)
                    if opcode == 2004:  # Legacy first handshake: flags, collection, skip, limit.
                        begin = body.index(b"\0", 4) + 9
                    elif opcode == 2013 and body[4] == 0:  # OP_MSG document section.
                        begin = 5
                    else:
                        raise AssertionError("Unexpected synthetic driver message")
                    size = struct.unpack_from("<i", body, begin)[0]
                    document = BSON(body[begin : begin + size]).decode()
                    command = next(iter(document)).lower()
                    if command in ("hello", "ismaster"):
                        reply = dict(
                            ok=1.0,
                            helloOk=True,
                            isWritablePrimary=True,
                            ismaster=True,
                            logicalSessionTimeoutMinutes=30,
                            minWireVersion=0,
                            maxWireVersion=21,
                            setName="synthetic",
                            hosts=[address],
                        )
                    elif command == "insert":
                        inserts.append((document["lsid"], document["txnNumber"]))
                        reply = dict(ok=1.0, n=1)
                    elif command == "committransaction":
                        commits.append((document["lsid"], document["txnNumber"]))
                        if len(commits) <= unacknowledged:
                            return  # No acknowledgement; outcome is deliberately unknown.
                        reply = dict(ok=1.0)
                    elif command == "endsessions":
                        reply = dict(ok=1.0)
                    else:
                        raise AssertionError("Unexpected synthetic command")
                    if opcode == 2004:
                        payload = struct.pack("<iqii", 0, 0, 0, 1) + BSON.encode(reply)
                        response_opcode = 1
                    else:
                        payload = b"\0" * 5 + BSON.encode(reply)
                        response_opcode = 2013
                    writer.write(
                        _HEADER.pack(len(payload) + _HEADER.size, 1, request_id, response_opcode)
                        + payload
                    )
                    await writer.drain()
            except asyncio.IncompleteReadError, ConnectionError:
                pass
            except Exception as exc:
                failures.append(exc)
            finally:
                writer.close()
                with suppress(ConnectionError):
                    await writer.wait_closed()
                sockets.discard(writer)
                handlers.discard(task)

        server = await asyncio.start_server(respond, "127.0.0.1", 0)
        address = f"127.0.0.1:{server.sockets[0].getsockname()[1]}"
        try:
            async with (
                asyncio.timeout(12),
                AsyncMongoClient(
                    f"mongodb://{address}/?replicaSet=synthetic",
                    retryWrites=False,
                    serverSelectionTimeoutMS=5000,
                    timeoutMS=timeout_ms,
                ) as client,
            ):
                async with client.start_session() as session:
                    await session.start_transaction(
                        read_concern=ReadConcern("snapshot"), write_concern=WriteConcern("majority")
                    )
                    await client.synthetic_db.owned_fixture.insert_one(
                        {"owned": True}, session=session
                    )
                    if confirmed:
                        await session.commit_transaction()
                    else:
                        with self.assertRaises(ConnectionFailure) as error:
                            await session.commit_transaction()
                        self.assertTrue(
                            error.exception.has_error_label("UnknownTransactionCommitResult")
                        )
        finally:
            server.close()
            for writer in tuple(sockets):
                writer.close()
            await server.wait_closed()
            await asyncio.gather(*tuple(handlers))
        self.assertEqual(failures, [])
        self.assertEqual(len(inserts), 1)
        self.assertEqual(commits, inserts * (unacknowledged + int(confirmed)))
