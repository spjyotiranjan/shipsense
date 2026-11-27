import unittest
from dataclasses import replace
from datetime import datetime, timedelta, tzinfo
from uuid import UUID, uuid4

from shipsense_domain.approval_policy import (
    ApprovalFacts,
    Candidate,
    VerifiedStepUp,
    assess_approval,
)
from shipsense_domain.authorization import ROLE_VERSION, Decision
from test_identity import HUMAN, NOW, TENANT, scope


class ApprovalPolicyTests(unittest.TestCase):
    def setUp(self):
        self.candidate = Candidate(
            scope=scope(),
            proposal_id=uuid4(),
            proposer_account_id=UUID(int=10),
            revision=1,
            action="operation.request",
            policy_version="synthetic-v1",
            expires_at=NOW + timedelta(minutes=15),
            provider_target="a" * 64,
            artifact="b" * 64,
            base_commit="c" * 64,
            diff="d" * 64,
            config="e" * 64,
            dependencies="f" * 64,
            verification="1" * 64,
            rollback="2" * 64,
        )
        self.correlation = uuid4()
        self.decision = Decision(
            uuid4(),
            True,
            "allowed",
            TENANT,
            HUMAN,
            "approval.decide",
            scope(),
            NOW,
            self.correlation,
        )
        self.step_up = VerifiedStepUp(uuid4(), HUMAN, self.candidate.digest(), NOW)
        self.facts = ApprovalFacts(
            decision=self.decision,
            account_id=UUID(int=11),
            session_id=self.step_up.session_id,
            environment_classification="nonproduction",
            step_up=self.step_up,
            authz_revision=2,
            tenant_authz_revision=3,
        )
        self.events = []

    def assess(self, candidate=None, facts=None, append=None):
        return assess_approval(
            candidate or self.candidate,
            self.candidate.digest(),
            facts or self.facts,
            NOW,
            append if append is not None else self.events.append,
        )

    def test_exact_version_has_bounded_eligibility_and_correlated_audit(self):
        result = self.assess()
        self.assertEqual(result.reason, "eligible")
        self.assertEqual(result.candidate_digest, self.candidate.digest())
        self.assertEqual(result.expires_at, NOW + timedelta(minutes=5))
        self.assertEqual(result.role_version, ROLE_VERSION)
        self.assertEqual((result.authz_revision, result.tenant_authz_revision), (2, 3))
        self.assertEqual(result.correlation_id, self.correlation)
        self.assertEqual(self.events, [result])

    def test_every_material_change_invalidates_prior_review(self):
        for name in (
            "provider_target",
            "artifact",
            "base_commit",
            "diff",
            "config",
            "dependencies",
            "verification",
            "rollback",
        ):
            with self.subTest(name=name):
                changed = Candidate.model_validate(self.candidate.model_dump() | {name: "3" * 64})
                self.assertEqual(self.assess(changed).reason, "candidate_changed")

    def test_actor_and_assurance_require_independent_human_and_bound_step_up(self):
        for changes, reason in (
            ({"account_id": self.candidate.proposer_account_id}, "self_approval"),
            ({"account_id": None}, "human_required"),
            ({"step_up": None}, "step_up_required"),
            ({"session_id": uuid4()}, "step_up_required"),
            ({"step_up": replace(self.step_up, at=NOW - timedelta(minutes=5))}, "step_up_required"),
            ({"environment_classification": "production"}, "policy_denied"),
        ):
            with self.subTest(changes=changes):
                result = self.assess(facts=replace(self.facts, **changes))
                self.assertEqual(result.reason, reason)
                self.assertIsNone(result.expires_at)
                self.assertEqual(self.events[-1], result)

    def test_wrong_scope_cannot_leave_candidate_identity_in_actor_audit(self):
        decision = replace(self.decision, scope=scope(uuid4()))
        result = self.assess(facts=replace(self.facts, decision=decision))
        self.assertEqual(result.reason, "not_found")
        self.assertIsNone(result.candidate_digest)
        self.assertIsNone(result.scope)
        self.assertEqual(self.events[-1], result)

    def test_step_up_uses_elapsed_time_across_a_repeated_hour(self):
        class RepeatedHour(tzinfo):
            def utcoffset(self, dt):
                return timedelta(hours=-5 if dt is not None and dt.fold else -4)

        zone = RepeatedHour()
        proof_at = datetime(2026, 11, 1, 1, 14, tzinfo=zone)
        now = datetime(2026, 11, 1, 1, 15, tzinfo=zone, fold=1)
        facts = replace(
            self.facts,
            decision=replace(self.decision, evaluated_at=now),
            step_up=replace(self.step_up, at=proof_at),
        )
        result = assess_approval(
            self.candidate, self.candidate.digest(), facts, now, self.events.append
        )
        self.assertEqual(result.reason, "step_up_required")
        self.assertIsNone(result.expires_at)

    def test_audit_failure_prevents_releasing_eligibility(self):
        def unavailable(_event):
            raise RuntimeError("AUDIT_UNAVAILABLE")

        with self.assertRaisesRegex(RuntimeError, "AUDIT_UNAVAILABLE"):
            self.assess(append=unavailable)
