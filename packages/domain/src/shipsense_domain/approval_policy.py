"""Offline, exact-version approval evaluation; not an approval ledger or effect permit."""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from shipsense_domain.authorization import ROLE_VERSION, Decision
from shipsense_domain.models import Contract, Revision, ServiceEnvironmentScope, Timestamp

POLICY_VERSION = "synthetic-v1"
STEP_UP_WINDOW = timedelta(minutes=5)
Digest = Annotated[str, Field(strict=True, pattern=r"^[0-9a-f]{64}$")]
Outcome = Literal[
    "not_found",
    "policy_denied",
    "candidate_changed",
    "candidate_expired",
    "human_required",
    "self_approval",
    "step_up_required",
    "eligible",
]


class Candidate(Contract):
    schema_version: Literal[1] = 1
    scope: ServiceEnvironmentScope
    proposal_id: UUID
    proposer_account_id: UUID
    revision: Revision
    action: Literal["operation.request"]
    policy_version: Annotated[str, Field(strict=True, min_length=1, max_length=64)]
    expires_at: Timestamp
    provider_target: Digest
    artifact: Digest
    base_commit: Digest
    diff: Digest
    config: Digest
    dependencies: Digest
    verification: Digest
    rollback: Digest

    def digest(self) -> str:
        canonical = json.dumps(
            self.model_dump(mode="json", by_alias=True),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(canonical.encode("ascii")).hexdigest()


@dataclass(frozen=True)
class VerifiedStepUp:
    """Internal verifier output; no verifier or credential is implemented here."""

    session_id: UUID
    principal_id: UUID
    candidate_digest: str
    at: datetime


@dataclass(frozen=True)
class ApprovalFacts:
    """Trusted, same-snapshot facts; only the expected digest may come from an input."""

    decision: Decision
    account_id: UUID | None
    session_id: UUID
    environment_classification: Literal["nonproduction", "production"]
    step_up: VerifiedStepUp | None
    authz_revision: int
    tenant_authz_revision: int


@dataclass(frozen=True)
class ApprovalAssessment:
    tenant_id: UUID
    scope: ServiceEnvironmentScope | None
    principal_id: UUID
    authorization_decision_id: UUID
    correlation_id: UUID
    assessed_at: datetime
    reason: Outcome
    candidate_digest: str | None
    expires_at: datetime | None
    policy_version: str
    role_version: str
    authz_revision: int
    tenant_authz_revision: int


def _reason(
    candidate: Candidate, digest: str, expected_digest: str, facts: ApprovalFacts, now: datetime
) -> Outcome:
    decision = facts.decision
    if (
        not decision.live_at(now)
        or decision.action != "approval.decide"
        or decision.scope != candidate.scope
        or decision.tenant_id != candidate.scope.tenant_id
        or now.utcoffset() is None
        or decision.evaluated_at.utcoffset() is None
        or decision.evaluated_at.astimezone(UTC) != now.astimezone(UTC)
    ):
        return "not_found"
    if (
        candidate.policy_version != POLICY_VERSION
        or decision.role_version != ROLE_VERSION
        or facts.environment_classification != "nonproduction"
    ):
        return "policy_denied"
    if digest != expected_digest:
        return "candidate_changed"
    if candidate.expires_at <= now:
        return "candidate_expired"
    if facts.account_id is None:
        return "human_required"
    if facts.account_id == candidate.proposer_account_id:
        return "self_approval"
    step_up = facts.step_up
    if (
        step_up is None
        or step_up.at.utcoffset() is None
        or step_up.session_id != facts.session_id
        or step_up.principal_id != decision.principal_id
        or step_up.candidate_digest != digest
    ):
        return "step_up_required"
    age = now.astimezone(UTC) - step_up.at.astimezone(UTC)
    if not timedelta(0) <= age < STEP_UP_WINDOW:
        return "step_up_required"
    return "eligible"


def assess_approval(
    candidate: Candidate,
    expected_digest: str,
    facts: ApprovalFacts,
    now: datetime,
    append: Callable[[ApprovalAssessment], None],
) -> ApprovalAssessment:
    """Append a redacted decision before returning; an assessment is not reusable authority."""
    digest = candidate.digest()
    reason = _reason(candidate, digest, expected_digest, facts, now)
    decision = facts.decision
    step_up = facts.step_up
    event = ApprovalAssessment(
        decision.tenant_id,
        candidate.scope if reason != "not_found" else None,
        decision.principal_id,
        decision.id,
        decision.correlation_id,
        now,
        reason,
        digest if reason != "not_found" else None,
        min(
            candidate.expires_at,
            step_up.at.astimezone(UTC) + STEP_UP_WINDOW,
            decision.expires_at.astimezone(UTC),
        )
        if reason == "eligible" and step_up is not None and decision.expires_at is not None
        else None,
        POLICY_VERSION,
        ROLE_VERSION,
        facts.authz_revision,
        facts.tenant_authz_revision,
    )
    append(event)
    return event
