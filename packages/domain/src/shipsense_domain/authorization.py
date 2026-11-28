"""Deny-before-fetch authorization over freshly resolved canonical state.

No transport authenticators or persistence adapters are enabled by this module.
Only trusted callers may construct PrincipalContext after credential validation.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Literal, Protocol
from uuid import UUID, uuid4

from shipsense_domain.models import (
    Action,
    HumanPrincipal,
    IdentityContract,
    PrincipalSubject,
    ResourceScope,
    Role,
    RoleGrant,
    ServiceAccount,
    TeamSubject,
)

ROLE_VERSION = "p02-exact-v1"
# Exact scopes only. No parent expansion or production effect authority is implied.
ROLE_CAPABILITIES: Mapping[Role, frozenset[Action]] = MappingProxyType(
    {
        "reader": frozenset({"metadata.read", "evidence.read"}),
        "developer": frozenset(
            {"metadata.read", "evidence.read", "proposal.create", "operation.request"}
        ),
        "operator": frozenset(
            {
                "metadata.read",
                "evidence.read",
                "proposal.create",
                "investigation.create",
                "operation.request",
            }
        ),
        "securityReviewer": frozenset({"security.read", "audit.read"}),
        "approver": frozenset({"approval.decide"}),
        "tenantAdministrator": frozenset({"identity.manage"}),
        "auditReader": frozenset({"audit.read"}),
        "serviceAccount": frozenset(),
    }
)


@dataclass(frozen=True)
class PrincipalContext:
    principal_id: UUID
    tenant_id: UUID
    authz_revision: int
    tenant_authz_revision: int
    expires_at: datetime


@dataclass(frozen=True)
class Decision:
    id: UUID
    allowed: bool
    reason: Literal["allowed", "not_found"]
    tenant_id: UUID
    principal_id: UUID
    action: Action
    scope: ResourceScope | None
    evaluated_at: datetime
    correlation_id: UUID
    role_version: str = ROLE_VERSION
    expires_at: datetime | None = None

    def live_at(self, now: datetime) -> bool:
        return (
            self.allowed and self.expires_at is not None and before_deadline(now, self.expires_at)
        )


class AuthorityStore(Protocol):
    """Load current tenant state using a validated internal context, never HTTP claims.

    The adapter must enforce tenant filters in storage, return no other tenant,
    validate record integrity and use the authoritative authorization fence.
    None represents hidden/missing; dependency failure must raise, never allow.
    """

    def current(self, context: PrincipalContext) -> IdentityContract | None: ...


class AuditWriter(Protocol):
    """Append only. Failure must prevent returning protected data or authority."""

    def append_decision(self, decision: Decision) -> None: ...


class ScopedReader(Protocol):
    """Every implementation query includes the entire scope, never fetch-then-filter."""

    def metadata(self, scope: ResourceScope, object_id: UUID) -> dict[str, str] | None: ...


class HiddenResource(Exception):
    """Same public outcome for denied and nonexistent resources."""


def before_deadline(now: datetime, deadline: datetime) -> bool:
    return (
        now.utcoffset() is not None
        and deadline.utcoffset() is not None
        and now.astimezone(UTC) < deadline.astimezone(UTC)
    )


def scope_exists(state: IdentityContract, scope: ResourceScope) -> bool:
    if scope.tenant_id != state.organization.id or state.organization.status != "active":
        return False
    if scope.kind == "organization":
        return True
    if not any(
        p.id == scope.project_id and p.tenant_id == scope.tenant_id and p.status == "active"
        for p in state.projects
    ):
        return False
    if scope.kind in ("service", "serviceEnvironment") and not any(
        s.id == scope.service_id
        and s.tenant_id == scope.tenant_id
        and s.project_id == scope.project_id
        and s.status == "active"
        for s in state.services
    ):
        return False
    if scope.kind in ("environment", "serviceEnvironment") and not any(
        e.id == scope.environment_id
        and e.tenant_id == scope.tenant_id
        and e.project_id == scope.project_id
        and e.status == "active"
        for e in state.environments
    ):
        return False
    return scope.kind != "serviceEnvironment" or any(
        b.tenant_id == scope.tenant_id
        and b.project_id == scope.project_id
        and b.service_id == scope.service_id
        and b.environment_id == scope.environment_id
        and b.status == "active"
        for b in state.service_environments
    )


def grant_applies(
    state: IdentityContract,
    context: PrincipalContext,
    grant: RoleGrant,
    scope: ResourceScope,
    action: Action,
    now: datetime,
) -> bool:
    if (
        grant.tenant_id != context.tenant_id
        or grant.scope != scope
        or grant.status != "active"
        or not before_deadline(now, grant.expires_at)
        or grant.role_version != ROLE_VERSION
    ):
        return False
    if isinstance(grant.subject, PrincipalSubject):
        matches = grant.subject.principal_id == context.principal_id
    else:
        matches = (
            isinstance(grant.subject, TeamSubject)
            and any(
                team.id == grant.subject.team_id
                and team.tenant_id == context.tenant_id
                and team.status == "active"
                for team in state.teams
            )
            and any(
                membership.tenant_id == context.tenant_id
                and membership.team_id == grant.subject.team_id
                and membership.principal_id == context.principal_id
                and membership.status == "active"
                for membership in state.team_memberships
            )
        )
    principal = next((p for p in state.principals if p.id == context.principal_id), None)
    if isinstance(principal, ServiceAccount):
        return (
            matches
            and grant.role == "serviceAccount"
            and action in grant.action_allowlist
            and before_deadline(now, principal.expires_at)
        )
    return (
        matches
        and isinstance(principal, HumanPrincipal)
        and action in ROLE_CAPABILITIES[grant.role]
    )


class AuthorizationService:
    def __init__(self, authority: AuthorityStore, audit: AuditWriter) -> None:
        self._authority = authority
        self._audit = audit

    def evaluate(
        self,
        context: PrincipalContext,
        action: Action,
        scope: ResourceScope,
        now: datetime,
        correlation_id: UUID,
    ) -> Decision:
        expiration = None
        # Reject untrusted/mismatched scope before touching any tenant store.
        if before_deadline(now, context.expires_at) and context.tenant_id == scope.tenant_id:
            state = self._authority.current(context)
            if state is not None and scope_exists(state, scope):
                principal = next(
                    (p for p in state.principals if p.id == context.principal_id), None
                )
                if (
                    principal is not None
                    and principal.status == "active"
                    and principal.tenant_id == context.tenant_id
                    and principal.authz_revision == context.authz_revision
                    and state.organization.authz_revision == context.tenant_authz_revision
                ):
                    latest_grant = max(
                        (
                            grant.expires_at.astimezone(UTC)
                            for grant in state.role_grants
                            if grant_applies(state, context, grant, scope, action, now)
                        ),
                        default=None,
                    )
                    if latest_grant is not None:
                        expiration = min(context.expires_at.astimezone(UTC), latest_grant)
                        if isinstance(principal, ServiceAccount):
                            expiration = min(expiration, principal.expires_at.astimezone(UTC))
        allowed = expiration is not None
        decision = Decision(
            uuid4(),
            allowed,
            "allowed" if allowed else "not_found",
            context.tenant_id,
            context.principal_id,
            action,
            scope if allowed else None,
            now,
            correlation_id,
            expires_at=expiration,
        )
        # No result (even a denial receipt) is presented as durably audited if this fails.
        self._audit.append_decision(decision)
        return decision

    def read_metadata(
        self,
        context: PrincipalContext,
        scope: ResourceScope,
        object_id: UUID,
        reader: ScopedReader,
        now: datetime,
        correlation_id: UUID,
    ) -> dict[str, str]:
        decision = self.evaluate(context, "metadata.read", scope, now, correlation_id)
        if not decision.allowed:
            raise HiddenResource()
        result = reader.metadata(scope, object_id)
        if result is None:
            raise HiddenResource()
        return result
