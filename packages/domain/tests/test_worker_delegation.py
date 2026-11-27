"""No-effect queue admission exercised with test-owned identity and credentials."""

import unittest
from dataclasses import replace
from datetime import timedelta
from uuid import UUID

from shipsense_domain.authorization import AuthorizationService, HiddenResource, PrincipalContext
from shipsense_domain.models import ResourceScope
from shipsense_domain.scoped_queries import MetadataGateway
from test_identity import HUMAN, NOW, PROD, TENANT, Audit, Authority, fixture, grant, scope

JOB, DELEGATION, WORKER, CORRELATION = (UUID(int=i) for i in range(101, 105))


class WorkerDelegationTests(unittest.TestCase):
    def test_grant_expiring_during_audit_prevents_retrieval(self):
        from shipsense_domain.worker_delegation import (
            DelegatedCount,
            Delegation,
            VerifiedWorker,
            WorkerCountHarness,
        )

        now = NOW
        expiry = NOW + timedelta(seconds=5)
        later = NOW + timedelta(minutes=1)

        class SlowAudit(Audit):
            def append_decision(self, decision):
                nonlocal now
                super().append_decision(decision)
                now = expiry

        class Index:
            def count(self, scope: ResourceScope) -> int:
                raise AssertionError("Expired grant allowed retrieval")

            def suggestions(self, scope: ResourceScope, prefix: str) -> tuple[str, ...]:
                raise AssertionError("This harness only permits counts.")

        store = Authority(fixture(roleGrants=[grant(expiresAt=expiry)]))
        gateway = MetadataGateway(AuthorizationService(store, SlowAudit()), Index(), lambda: now)
        worker = VerifiedWorker(WORKER, TENANT, "shipsense-worker", later)
        delegation = Delegation(
            JOB,
            DELEGATION,
            WORKER,
            scope(),
            later,
            True,
            PrincipalContext(HUMAN, TENANT, 1, 1, later),
        )
        harness = WorkerCountHarness(lambda _: worker, lambda *_: delegation, gateway, lambda: now)
        with self.assertRaises(HiddenResource):
            harness.count(
                "test credential",
                DelegatedCount(job_id=JOB, delegation_id=DELEGATION, scope=scope()),
                CORRELATION,
            )

    def test_only_current_bound_delegation_reaches_the_audited_scoped_count(self):
        from shipsense_domain.worker_delegation import (
            DelegatedCount,
            Delegation,
            VerifiedWorker,
            WorkerCountHarness,
        )

        envelope = dict(jobId=JOB, delegationId=DELEGATION, scope=scope())
        work = DelegatedCount.model_validate(envelope)
        future = NOW + timedelta(seconds=30)
        credential = VerifiedWorker(WORKER, TENANT, "shipsense-worker", future)
        current = Delegation(
            JOB,
            DELEGATION,
            WORKER,
            scope(),
            future,
            True,
            PrincipalContext(HUMAN, TENANT, 1, 1, future),
        )
        lookups, reads = [], []

        class Index:
            def count(self, scope: ResourceScope) -> int:
                reads.append(scope)
                return 7

            def suggestions(self, scope: ResourceScope, prefix: str) -> tuple[str, ...]:
                raise AssertionError("This harness only permits counts.")

        def resolve(tenant_id, job_id, delegation_id):
            lookups.append((tenant_id, job_id, delegation_id))
            return current

        audit = Audit()
        store = Authority(fixture())
        gateway = MetadataGateway(AuthorizationService(store, audit), Index(), lambda: NOW)
        harness = WorkerCountHarness(lambda _: credential, resolve, gateway, lambda: NOW)
        for invalid_worker in (
            None,
            replace(credential, audience="shipsense-bff"),
            replace(credential, expires_at=NOW),
            replace(credential, tenant_id=UUID(int=900)),
        ):
            with self.subTest(credential=invalid_worker), self.assertRaises(HiddenResource):
                WorkerCountHarness(lambda _: invalid_worker, resolve, gateway, lambda: NOW).count(
                    "test credential", work, CORRELATION
                )
        self.assertEqual(lookups, [])

        valid = current
        for invalid in (
            None,
            replace(valid, job_id=DELEGATION),
            replace(valid, delegation_id=JOB),
            replace(valid, worker_id=JOB),
            replace(valid, scope=scope(PROD)),
            replace(valid, expires_at=NOW),
            replace(valid, active=False),
            replace(valid, principal=replace(valid.principal, tenant_id=UUID(int=901))),
        ):
            current = invalid
            with self.subTest(delegation=invalid), self.assertRaises(HiddenResource):
                harness.count("test credential", work, CORRELATION)
        self.assertTrue(all(item == (TENANT, JOB, DELEGATION) for item in lookups))
        self.assertEqual(store.calls, 0)
        self.assertEqual(reads, [])

        current = valid
        self.assertEqual(harness.count("test credential", work, CORRELATION), 7)
        self.assertEqual(audit.events[-1].correlation_id, CORRELATION)
        self.assertTrue(audit.events[-1].allowed)
        current = replace(valid, active=False)
        with self.assertRaises(HiddenResource):
            harness.count("test credential", work, CORRELATION)
        current = valid
        store.state = fixture(roleGrants=[])
        with self.assertRaises(HiddenResource):
            harness.count("test credential", work, CORRELATION)
        self.assertFalse(audit.events[-1].allowed)
        self.assertIsNone(audit.events[-1].scope)
        self.assertEqual(reads, [scope()])

        # An otherwise valid admission cannot release a count after its deadline.
        store.state = fixture()
        clock_values = iter((NOW, NOW, future))
        expiring = WorkerCountHarness(
            lambda _: credential, resolve, gateway, lambda: next(clock_values)
        )
        with self.assertRaises(HiddenResource):
            expiring.count("test credential", work, CORRELATION)
        self.assertEqual(reads, [scope(), scope()])

        now = NOW

        class SlowAudit(Audit):
            def append_decision(self, decision):
                nonlocal now
                super().append_decision(decision)
                now = future

        slow_gateway = MetadataGateway(
            AuthorizationService(store, SlowAudit()), Index(), lambda: now
        )
        expiring = WorkerCountHarness(lambda _: credential, resolve, slow_gateway, lambda: now)
        with self.assertRaises(HiddenResource):
            expiring.count("test credential", work, CORRELATION)
        self.assertEqual(reads, [scope(), scope()])
