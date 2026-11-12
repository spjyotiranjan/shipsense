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
        self.failure = None
        self.pause = None
        self.entered = asyncio.Event()
        self.lookups = []

    @asynccontextmanager
    async def begin(self):
        async with self.lock:
            pending = self.record
            events = []
            store = self

            class Transaction:
                async def session(self, digest):
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
                    return store.identity

                async def replace(self, expected, replacement):
                    nonlocal pending
                    if pending != expected or replacement != revoke_session(
                        expected, replacement.revoked_at
                    ):
                        raise RuntimeError("conflict")
                    pending = replacement

                async def append(self, event):
                    if store.failure == "audit":
                        raise RuntimeError("private audit details")
                    events.append(event)

            yield Transaction()
            if self.failure == "commit":
                raise RuntimeError("private commit details")
            self.record = pending
            self.events.extend(events)


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
        first = await self.authority.resolve(HANDLE, "resolve-1")
        self.now += 10
        self.assertEqual(await self.authority.resolve(HANDLE, "resolve-2"), first)
        self.assertEqual(self.store.record, self.record)
        self.assertEqual(self.store.lookups, [handle_digest(HANDLE)] * 2)
        wire = json.dumps([e.model_dump(mode="json") for e in self.store.events])
        for forbidden in [HANDLE, handle_digest(HANDLE), str(self.account.account_id)]:
            self.assertNotIn(forbidden, wire + first.model_dump_json())
        self.assertEqual([e.correlation_id for e in self.store.events], ["resolve-1", "resolve-2"])
        self.assertEqual(len({e.event_id for e in self.store.events}), 2)

    async def test_idempotent_revoke_and_unknown_handle(self):
        await self.authority.revoke(HANDLE, "logout")
        revoked = self.store.record
        await self.authority.revoke(HANDLE, "logout-retry")
        await self.authority.revoke("x" * 43, "unknown")
        self.assertIs(self.store.record, revoked)
        with self.assertRaises(SessionDenied):
            await self.authority.resolve(HANDLE, "after-logout")
        self.assertEqual([e.outcome for e in self.store.events], ["revoked"] * 3 + ["denied"])

    async def test_all_denials_have_same_audit_shape(self):
        cases = [
            None,
            self.record_with(revoked_at=self.now),
            self.record_with(idle_expires_at=self.now),
            self.record_with(absolute_expires_at=self.now),
        ]
        for record in cases:
            self.store.record = record
            with self.assertRaises(SessionDenied):
                await self.authority.resolve(HANDLE, "same-request")
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
                correlation_id="valid",
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
        headers = {"Authorization": "Bearer " + token, "X-Request-ID": "canonical-api"}
        path = "/internal/v1/auth/session/resolve"
        with TestClient(create_app(session_authority=self.authority, service_keys=keys)) as client:
            self.assertEqual(
                client.post(path, json={"handle": HANDLE}, headers=headers).status_code, 200
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
                denied[0], (401, {"state": "denied", "requestId": "canonical-api"}, "no-store")
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
