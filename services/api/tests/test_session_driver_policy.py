import asyncio
import unittest
from unittest.mock import AsyncMock, Mock
from uuid import UUID

from pymongo.errors import AutoReconnect
from shipsense_api.session_driver_policy import PinnedSessionDriverPolicy
from shipsense_api.session_storage_transactions import CommitOutcome


class DriverPolicyTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = Mock()
        self.client.options = Mock(
            timeout=None, retry_reads=False, retry_writes=False, max_adaptive_retries=0
        )
        self.db = Mock(client=self.client)
        self.session = Mock(
            client=self.client,
            in_transaction=True,
            start_transaction=AsyncMock(),
            commit_transaction=AsyncMock(),
            end_session=AsyncMock(),
        )
        self.client.start_session.return_value = self.session
        self.policy = PinnedSessionDriverPolicy(self.db, UUID(int=1))

    def test_rejects_automatic_retry_and_client_side_timeout_modes(self):
        for setting, value in (
            ("timeout", 0.5),
            ("retry_reads", True),
            ("retry_writes", True),
            ("max_adaptive_retries", 1),
        ):
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                self.client.options = Mock(
                    **(
                        {
                            "timeout": None,
                            "retry_reads": False,
                            "retry_writes": False,
                            "max_adaptive_retries": 0,
                        }
                        | {setting: value}
                    )
                )
                PinnedSessionDriverPolicy(self.db, UUID(int=1))

    async def test_transaction_concerns_and_cleanup(self):
        deadline = asyncio.get_running_loop().time() + 1
        async with self.policy.open(deadline=deadline, cleanup_limit=0.25) as session:
            self.assertIs(session, self.session)
            self.session.end_session.assert_not_awaited()
        options = self.session.start_transaction.await_args.kwargs
        self.assertEqual(options["read_preference"].name, "Primary")
        self.assertEqual(options["read_concern"].level, "snapshot")
        self.assertEqual(options["write_concern"].document, {"w": "majority"})
        self.session.end_session.assert_awaited_once()

    async def test_commit_confirmation_and_unknown_are_distinct(self):
        deadline = asyncio.get_running_loop().time() + 1
        result = await self.policy.commit(self.session, deadline=deadline, send_limit=0.5)
        self.assertIs(result, CommitOutcome.CONFIRMED_COMMIT)
        self.session.commit_transaction.reset_mock()
        self.session.commit_transaction.side_effect = AutoReconnect("synthetic lost ack")
        result = await self.policy.commit(self.session, deadline=deadline, send_limit=0.5)
        self.assertIs(result, CommitOutcome.UNKNOWN)
        self.session.commit_transaction.assert_awaited_once()

    async def test_stalled_commit_times_out_without_an_outer_retry(self):
        async def stall():
            await asyncio.Future()

        self.session.commit_transaction.side_effect = stall
        deadline = asyncio.get_running_loop().time() + 1
        result = await self.policy.commit(self.session, deadline=deadline, send_limit=0.01)
        self.assertIs(result, CommitOutcome.UNKNOWN)
        self.session.commit_transaction.assert_awaited_once()
