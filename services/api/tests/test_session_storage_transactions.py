import asyncio
import unittest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

from shipsense_api.session_authority import CanonicalSessionAuthority
from shipsense_api.session_bridge import AuthorityUnavailable
from shipsense_api.session_storage_body import StorageBodyFailed
from shipsense_api.session_storage_transactions import CommitOutcome, MongoSessionTransactions
from shipsense_domain.sessions import SessionDenied, handle_digest
from test_session_storage_body import StorageFixture

_HANDLE = "a" * 43


class StorageTransactionTests(StorageFixture, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        self.lifecycle_calls = []
        self.commit = AsyncMock(return_value=CommitOutcome.CONFIRMED_COMMIT)
        self.adapter = MongoSessionTransactions(self.db, self)
        self.authority = CanonicalSessionAuthority(self.adapter, clock=lambda: 1200)
        self.sessions.find_one_and_update.return_value["_id"] = handle_digest(_HANDLE)
        self.cleanup_started = asyncio.Event()
        self.cleanup_wait = None

    @asynccontextmanager
    async def open(self, *, deadline, cleanup_limit):
        self.assertGreater(deadline, asyncio.get_running_loop().time())
        self.assertEqual(cleanup_limit, 0.25)
        self.lifecycle_calls.append("opened")
        try:
            yield self.tx
        finally:
            self.lifecycle_calls.append("closed")
            self.cleanup_started.set()
            if self.cleanup_wait is not None:
                await self.cleanup_wait.wait()

    async def test_no_policy_means_no_storage_access(self):
        authority = CanonicalSessionAuthority(MongoSessionTransactions(self.db))
        with self.assertRaises(AuthorityUnavailable):
            await authority.resolve(_HANDLE, "fixture")
        self.db.__getitem__.assert_not_called()
        self.commit.assert_not_awaited()

    async def test_no_receipt_never_commits(self):
        with self.assertRaises(StorageBodyFailed):
            async with self.adapter.begin():
                pass
        self.commit.assert_not_awaited()

    async def test_denial_receipt_commits_once_before_denial_is_released(self):
        self.sessions.find_one_and_update.return_value = None
        with self.assertRaises(SessionDenied):
            await self.authority.resolve(_HANDLE, "fixture")
        self.append_receipt.assert_awaited_once()
        self.commit.assert_awaited_once()
        args, options = self.commit.await_args
        self.assertEqual(args, (self.tx,))
        self.assertEqual(options["send_limit"], 0.5)
        self.assertLessEqual(options["deadline"] - asyncio.get_running_loop().time(), 2.0)
        self.assertEqual(self.lifecycle_calls, ["opened", "closed"])

    async def test_unknown_commit_is_not_retried_or_reported_as_success(self):
        self.sessions.find_one_and_update.return_value = None
        self.commit.return_value = CommitOutcome.UNKNOWN
        with self.assertRaises(AuthorityUnavailable):
            await self.authority.revoke(_HANDLE, "fixture")
        self.sessions.find_one_and_update.assert_awaited_once()
        self.append_receipt.assert_awaited_once()
        self.commit.assert_awaited_once()
        self.assertEqual(self.lifecycle_calls, ["opened", "closed"])

    async def test_cancelled_commit_is_not_retried_or_reported_as_success(self):
        self.sessions.find_one_and_update.return_value = None
        started = asyncio.Event()

        async def wait_for_commit(*_args, **_kwargs):
            started.set()
            await asyncio.Future()

        self.commit.side_effect = wait_for_commit
        task = asyncio.create_task(self.authority.revoke(_HANDLE, "fixture"))
        await asyncio.wait_for(started.wait(), 1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.append_receipt.assert_awaited_once()
        self.commit.assert_awaited_once()
        self.assertEqual(self.lifecycle_calls, ["opened", "closed"])

    async def test_deadline_during_body_does_not_call_commit(self):
        async def slow_lookup(*_args, **_kwargs):
            await asyncio.Future()

        self.sessions.find_one_and_update.side_effect = slow_lookup
        with (
            patch("shipsense_api.session_storage_transactions._OPERATION_LIMIT", 0.05),
            self.assertRaises(AuthorityUnavailable),
        ):
            await self.authority.revoke(_HANDLE, "fixture")
        self.commit.assert_not_awaited()
        self.append_receipt.assert_not_awaited()
        self.assertEqual(self.lifecycle_calls, ["opened", "closed"])

    async def test_valid_resolve_candidate_released_only_after_confirmed_commit(self):
        snapshot = await self.authority.resolve(_HANDLE, "fixture")
        self.assertEqual(snapshot.absoluteExpiresAt, 1900)
        self.assertEqual(self.append_receipt.await_args_list[-1].args[1]["outcome"], "allowed")
        for outcome in (CommitOutcome.CONFIRMED_ABORT, CommitOutcome.UNKNOWN):
            self.commit.return_value = outcome
            with self.subTest(outcome=outcome), self.assertRaises(AuthorityUnavailable):
                await self.authority.resolve(_HANDLE, "fixture")
            self.assertEqual(self.append_receipt.await_args_list[-1].args[1]["outcome"], "allowed")
        self.assertEqual(self.commit.await_count, 3)

    async def test_valid_resolve_candidate_is_withheld_on_failed_audit(self):
        self.append_receipt.return_value = False
        with self.assertRaises(AuthorityUnavailable):
            await self.authority.resolve(_HANDLE, "fixture")
        self.assertEqual(self.append_receipt.await_args_list[-1].args[1]["outcome"], "allowed")
        self.commit.assert_not_awaited()

    async def test_valid_resolve_candidate_is_withheld_on_cancellation_after_commit(self):
        self.cleanup_wait = asyncio.Event()
        task = asyncio.create_task(self.authority.resolve(_HANDLE, "fixture"))
        try:
            await asyncio.wait_for(self.cleanup_started.wait(), 1)
            self.commit.assert_awaited_once()
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
