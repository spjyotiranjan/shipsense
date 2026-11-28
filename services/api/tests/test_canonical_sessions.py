"""Synthetic fenced transaction proof only; no database durability/concurrency claim."""

import asyncio
import json
import time
import unittest
from contextlib import asynccontextmanager
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from pydantic import ValidationError
from shipsense_api.main import create_app
from shipsense_api.service_credentials import ServiceKey
from shipsense_api.session_authority import CanonicalSessionAuthority
from shipsense_api.session_bridge import AuthorityUnavailable, SessionDenied
from shipsense_domain.sessions import (
    SessionAccount,
    SessionAudit,
    SessionRecord,
    handle_digest,
    resolve_session,
    revoke_session,
)

HANDLE = "s" * 43


class SyntheticTransactions:
    """Test-only copy-on-commit store, with explicit fenced serialization."""

    def __init__(self, record, account):
        self.record = record
        self.identity = account
        self.events = []
        self.lock = asyncio.Lock()
        self.failure: str | None = None
        self.pause = None
        self.entered = asyncio.Event()
        self.commit_ack: asyncio.Event | None = None
        self.applied = asyncio.Event()
        self.lookups = []
        self.calls = []

    @asynccontextmanager
    async def begin(self):
        async with self.lock:
            pending = self.record
            events = []
            store = self

            class Transaction:
                async def session(self, digest):
                    store.calls.append(("session", digest))
                    store.lookups.append(digest)
                    if store.failure == "read":
                        raise RuntimeError("private database details")
                    store.entered.set()
                    if store.pause is not None:
                        await store.pause.wait()
                    return (
                        pending if pending is not None and pending.handle_digest == digest else None
                    )

                async def account(self, account_id):
                    store.calls.append(("account", account_id))
                    return store.identity

                async def replace(self, expected, replacement):
                    nonlocal pending
                    store.calls.append(("replace", expected.handle_digest))
                    if pending != expected or replacement != revoke_session(
                        expected, replacement.revoked_at
                    ):
                        raise RuntimeError("conflict")
                    pending = replacement

                async def append(self, event):
                    store.calls.append(("append", event.correlation_id))
                    if store.failure == "audit":
                        raise RuntimeError("private audit details")
                    events.append(event)

            yield Transaction()
            failure = self.failure
            if failure == "commit":
                raise RuntimeError("private commit details")
            self.record = pending
            self.events.extend(events)
            self.applied.set()
            if self.commit_ack is not None:
                await self.commit_ack.wait()
            if failure == "commit-ack-lost":
                raise RuntimeError("unconfirmed commit")


class CanonicalSessionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.now = int(time.time())
        self.record = SessionRecord(
            handle_digest=handle_digest(HANDLE),
            account_id=uuid4(),
            authentication_epoch=2,
            created_at=self.now - 300,
            last_activity_at=self.now - 100,
            absolute_expires_at=self.now + 600,
            idle_expires_at=self.now + 500,
            revision=1,
        )
        self.account = SessionAccount(
            account_id=self.record.account_id,
            authentication_epoch=2,
            status="active",
            revision=1,
        )
        self.store = SyntheticTransactions(self.record, self.account)
        self.authority = CanonicalSessionAuthority(self.store, lambda: self.now)

    def record_with(self, **changes):
        return SessionRecord.model_validate({**self.record.model_dump(), **changes})

    def account_with(self, **changes):
        return SessionAccount.model_validate({**self.account.model_dump(), **changes})

    def test_strict_immutable_records_and_time_bounds(self):
        for change in [
            {"revision": True},
            {"authentication_epoch": "2"},
            {"created_at": -1},
            {"extra": "ignored?"},
            {"handle_digest": HANDLE},
            {"absolute_expires_at": self.now + 601},
            {"idle_expires_at": self.now + 501},
            {"revoked_at": self.now - 301},
            {"last_activity_at": self.now + 600},
        ]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                self.record_with(**change)
        with self.assertRaises(ValidationError):
            self.record.revision = 2
        for bad in ["", "x" * 42, "x" * 44, "!" * 43, "é" * 43]:
            with self.assertRaises(SessionDenied):
                handle_digest(bad)
        self.assertEqual(len(handle_digest(HANDLE)), 64)
        self.assertNotIn(handle_digest(HANDLE), repr(self.record))

    def test_pure_deadlines_account_and_revocation_rules(self):
        self.assertIs(resolve_session(self.record, self.account, self.now), self.record)
        invalid = [
            (None, self.account, self.now),
            (self.record, None, self.now),
            (self.record, self.account_with(account_id=uuid4()), self.now),
            (self.record, self.account_with(status="suspended"), self.now),
            (self.record, self.account_with(status="archived"), self.now),
            (self.record, self.account_with(authentication_epoch=3), self.now),
            (self.record_with(revoked_at=self.now), self.account, self.now),
            (self.record, self.account, self.record.idle_expires_at),
            (self.record, self.account, self.record.absolute_expires_at),
            (self.record, self.account, self.record.last_activity_at - 1),
        ]
        for args in invalid:
            with self.subTest(args=args), self.assertRaises(SessionDenied):
                resolve_session(*args)
        revoked = revoke_session(self.record, self.now)
        self.assertEqual(revoked.revision, 2)
        self.assertEqual(
            revoked.model_dump(exclude={"revoked_at", "revision"}),
            self.record.model_dump(exclude={"revoked_at", "revision"}),
        )
        self.assertIs(revoke_session(revoked, self.now + 1), revoked)

    async def test_resolve_does_not_slide_and_commits_redacted_audit(self):
        correlation = [str(uuid4()), str(uuid4())]
        first = await self.authority.resolve(HANDLE, correlation[0])
        self.now += 10
        self.assertEqual(await self.authority.resolve(HANDLE, correlation[1]), first)
        self.assertEqual(self.store.record, self.record)
        self.assertEqual(self.store.lookups, [handle_digest(HANDLE)] * 2)
        wire = json.dumps([e.model_dump(mode="json") for e in self.store.events])
        for forbidden in [HANDLE, handle_digest(HANDLE), str(self.account.account_id)]:
            self.assertNotIn(forbidden, wire + first.model_dump_json())
        self.assertEqual([e.correlation_id for e in self.store.events], correlation)
        self.assertEqual(len({e.event_id for e in self.store.events}), 2)

    async def test_direct_caller_cannot_put_handle_or_digest_in_correlation(self):
        for correlation in (HANDLE, handle_digest(HANDLE)):
            await self.authority.resolve(HANDLE, correlation)
            self.assertNotIn(correlation, self.store.events[-1].model_dump_json())

    async def test_resolve_withholds_snapshot_if_deadline_passes_during_commit(self):
        absolute_first = self.record_with(
            last_activity_at=self.now + 1, idle_expires_at=self.record.absolute_expires_at + 1
        )
        for record in [self.record, absolute_first]:
            deadline = min(record.idle_expires_at, record.absolute_expires_at)
            with self.subTest(deadline=deadline):
                observation = record.last_activity_at
                store = SyntheticTransactions(record, self.account)
                authority = CanonicalSessionAuthority(
                    store, lambda: deadline if store.applied.is_set() else observation
                )
                with self.assertRaises(SessionDenied):
                    await authority.resolve(HANDLE, "expired-at-release")
                # The receipt describes the fenced observation, not release to a caller.
                (receipt,) = store.events
                self.assertEqual((receipt.recorded_at, receipt.outcome), (observation, "allowed"))

    async def test_resolve_withholds_snapshot_without_commit_ack_even_if_receipt_exists(self):
        correlation = str(uuid4())
        self.store.failure = "commit-ack-lost"
        with self.assertRaises(AuthorityUnavailable):
            await self.authority.resolve(HANDLE, correlation)
        self.assertEqual(self.store.lookups, [handle_digest(HANDLE)])
        self.assertEqual([e.correlation_id for e in self.store.events], [correlation])

    async def test_cancellation_during_commit_ack_never_releases_snapshot(self):
        self.store.commit_ack = asyncio.Event()
        correlation = str(uuid4())
        task = asyncio.create_task(self.authority.resolve(HANDLE, correlation))
        await asyncio.wait_for(self.store.applied.wait(), timeout=2)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual([e.correlation_id for e in self.store.events], [correlation])

    async def test_idempotent_revoke_and_unknown_handle(self):
        first, repeated, unknown = (str(uuid4()) for _ in range(3))
        await self.authority.revoke(HANDLE, first)
        revoked = self.store.record
        await self.authority.revoke(HANDLE, repeated)
        await self.authority.revoke("x" * 43, unknown)
        self.assertEqual(
            self.store.calls,
            [
                ("session", self.record.handle_digest),
                ("account", self.record.account_id),
                ("replace", self.record.handle_digest),
                ("append", first),
                ("session", self.record.handle_digest),
                ("account", self.record.account_id),
                ("append", repeated),
                ("session", handle_digest("x" * 43)),
                ("append", unknown),
            ],
        )
        self.assertIs(self.store.record, revoked)
        with self.assertRaises(SessionDenied):
            await self.authority.resolve(HANDLE, "after-logout")
        self.assertEqual([e.outcome for e in self.store.events], ["revoked"] * 3 + ["denied"])

    async def test_revoke_withholds_mutation_on_missing_or_wrong_account_fence(self):
        for invalid in (None, self.account_with(account_id=uuid4())):
            self.store.identity = invalid
            with self.assertRaises(AuthorityUnavailable):
                await self.authority.revoke(HANDLE, "bad-fence")
            self.assertEqual(self.store.record, self.record)
            self.assertEqual(self.store.events, [])

    async def test_all_denials_have_same_audit_shape(self):
        correlation = str(uuid4())
        cases = [
            None,
            self.record_with(revoked_at=self.now),
            self.record_with(idle_expires_at=self.now),
            self.record_with(absolute_expires_at=self.now),
        ]
        for record in cases:
            self.store.record = record
            with self.assertRaises(SessionDenied):
                await self.authority.resolve(HANDLE, correlation)
        comparable = [e.model_dump(exclude={"event_id"}) for e in self.store.events]
        self.assertTrue(all(e == comparable[0] for e in comparable))

    async def test_storage_audit_commit_failure_withholds_resolve_and_rolls_back_revoke(self):
        for failure in ["read", "audit", "commit"]:
            for action in [self.authority.resolve, self.authority.revoke]:
                self.store.failure = failure
                with (
                    self.subTest(failure=failure, action=action),
                    self.assertRaises(AuthorityUnavailable),
                ):
                    await action(HANDLE, "failure")
                self.assertEqual(self.store.record, self.record)
                self.assertEqual(self.store.events, [])

    async def test_audit_schema_rejects_credential_metadata(self):
        with self.assertRaises(ValidationError):
            SessionAudit(
                event_id=uuid4(),
                action="session.resolve",
                outcome="allowed",
                recorded_at=self.now,
                correlation_id=str(uuid4()),
                handle=HANDLE,
            )

    async def test_concurrent_revoke_has_one_transition_and_distinct_attempt_receipts(self):
        await asyncio.gather(*(self.authority.revoke(HANDLE, f"revoke-{i}") for i in range(8)))
        self.assertEqual(self.store.record.revision, 2)
        self.assertEqual(len(self.store.events), 8)
        self.assertEqual(len({e.event_id for e in self.store.events}), 8)

    async def test_revoke_wins_fence_before_resolve(self):
        self.store.pause = asyncio.Event()
        revoke = asyncio.create_task(self.authority.revoke(HANDLE, "revoke-first"))
        await self.store.entered.wait()
        resolve = asyncio.create_task(self.authority.resolve(HANDLE, "resolve-second"))
        self.store.pause.set()
        await revoke
        with self.assertRaises(SessionDenied):
            await resolve

    async def test_epoch_change_wins_fence_before_resolve(self):
        async with self.store.lock:
            resolve = asyncio.create_task(self.authority.resolve(HANDLE, "epoch-changed"))
            self.store.identity = self.account_with(authentication_epoch=3, revision=2)
        with self.assertRaises(SessionDenied):
            await resolve

    def test_api_composition_denial_unavailability_redaction_and_default_disabled(self):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        keys = {"current": ServiceKey(pem, "active", self.now - 60, self.now + 600)}
        token = jwt.encode(
            dict(
                iss="shipsense-web",
                aud="shipsense-auth",
                sub="shipsense-bff",
                scope="session:resolve",
                iat=self.now,
                nbf=self.now,
                exp=self.now + 60,
                jti="canonical-session-api",
            ),
            private,
            algorithm="RS256",
            headers={"kid": "current"},
        )
        valid_id = str(uuid4())
        headers = {"Authorization": "Bearer " + token, "X-Request-ID": valid_id}
        path = "/internal/v1/auth/session/resolve"
        with TestClient(create_app(session_authority=self.authority, service_keys=keys)) as client:
            self.assertEqual(
                client.post(path, json={"handle": HANDLE}, headers=headers).status_code, 200
            )
            for correlation in (HANDLE, handle_digest(HANDLE)):
                with self.assertLogs("shipsense.diagnostics", level="INFO") as auth_logs:
                    response = client.post(
                        path,
                        json={"handle": HANDLE},
                        headers=headers | {"X-Request-ID": correlation},
                    )
                self.assertEqual(response.status_code, 422)
                self.assertNotIn(
                    correlation, response.text + str(response.headers) + str(auth_logs.output)
                )
            denied = []
            for record in [
                None,
                self.record_with(revoked_at=self.now),
                self.record_with(idle_expires_at=self.now),
            ]:
                self.store.record = record
                r = client.post(path, json={"handle": HANDLE}, headers=headers)
                denied.append((r.status_code, r.json(), r.headers["cache-control"]))
            self.assertTrue(all(r == denied[0] for r in denied))
            self.assertEqual(
                denied[0], (401, {"state": "denied", "requestId": valid_id}, "no-store")
            )
            self.store.record = self.record
            self.store.failure = "commit"
            with self.assertLogs("shipsense.diagnostics", level="INFO") as logs:
                r = client.post(path, json={"handle": HANDLE}, headers=headers)
            self.assertEqual(r.status_code, 503)
            for secret in [HANDLE, handle_digest(HANDLE), "private", str(self.account.account_id)]:
                self.assertNotIn(secret, r.text + str(logs.output))
        with TestClient(create_app(service_keys=keys)) as client:
            self.assertEqual(
                client.post(path, json={"handle": HANDLE}, headers=headers).status_code, 503
            )
