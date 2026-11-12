"""Referential validation over a single authoritative tenant snapshot.

Persistence must load the full snapshot and serialize authority changes in its
transaction. This validator supplies no atomicity or database migration proof.
"""

from datetime import datetime
from uuid import UUID

from shipsense_domain.models import (
    Environment,
    HumanPrincipal,
    IdentityContract,
    OrganizationScope,
    PrincipalSubject,
    Project,
    Record,
    Service,
    ServiceAccount,
    ServiceEnvironment,
    TeamSubject,
)


class IntegrityViolation(Exception):
    """Safe failure; never include foreign identifiers or database messages."""


def validate_identity(state: IdentityContract) -> None:
    tenant = state.organization.id
    collections = (
        state.teams,
        state.projects,
        state.services,
        state.environments,
        state.service_environments,
        state.principals,
        state.team_memberships,
        state.role_grants,
    )
    ids = [state.organization.id] + [record.id for group in collections for record in group]
    if len(ids) != len(set(ids)):
        raise IntegrityViolation("Duplicate identity.")
    for group in collections:
        if any(record.tenant_id != tenant for record in group):
            raise IntegrityViolation("Invalid tenant reference.")
    teams = {item.id: item for item in state.teams}
    projects = {item.id: item for item in state.projects}
    services = {item.id: item for item in state.services}
    environments = {item.id: item for item in state.environments}
    principals = {item.id: item for item in state.principals}
    for record in (state.organization, *(r for group in collections for r in group)):
        require_creator = principals.get(record.created_by_principal_id)
        if require_creator is None:
            raise IntegrityViolation("Invalid creator reference.")

    def require(records: dict[UUID, Record], key: UUID, active: bool) -> None:
        record = records.get(key)
        if record is None or (active and record.status != "active"):
            raise IntegrityViolation("Invalid ownership or lifecycle reference.")

    # Case-insensitive names are unique within their documented scope, including
    # archived rows: archival never makes an identity/name silently reusable.
    for names in (
        [(item.name.casefold(),) for item in state.teams],
        [(item.name.casefold(),) for item in state.projects],
        [(item.project_id, item.name.casefold()) for item in state.services],
        [(item.project_id, item.name.casefold()) for item in state.environments],
        [
            (item.project_id, item.service_id, item.environment_id)
            for item in state.service_environments
        ],
        [(item.team_id, item.principal_id) for item in state.team_memberships],
        [(item.account_id,) for item in state.principals if isinstance(item, HumanPrincipal)],
        [
            (item.issuer, item.subject)
            for item in state.principals
            if isinstance(item, ServiceAccount)
        ],
    ):
        if len(names) != len(set(names)):
            raise IntegrityViolation("Duplicate identity or relationship.")
    for team in state.teams:
        require(dict(principals), team.owner_principal_id, team.status == "active")
    owned: tuple[Project | Service, ...] = (*state.projects, *state.services)
    for owned_item in owned:
        require(dict(teams), owned_item.owner_team_id, owned_item.status == "active")
    resources: tuple[Service | Environment | ServiceEnvironment, ...] = (
        *state.services,
        *state.environments,
        *state.service_environments,
    )
    for resource in resources:
        require(dict(projects), resource.project_id, resource.status == "active")
    for binding in state.service_environments:
        require(dict(services), binding.service_id, binding.status == "active")
        require(dict(environments), binding.environment_id, binding.status == "active")
        if (
            services[binding.service_id].project_id != binding.project_id
            or environments[binding.environment_id].project_id != binding.project_id
        ):
            raise IntegrityViolation("Invalid ancestry.")
    for principal in state.principals:
        if isinstance(principal, ServiceAccount):
            require(dict(teams), principal.owner_team_id, principal.status == "active")
    for membership in state.team_memberships:
        require(dict(teams), membership.team_id, membership.status == "active")
        require(dict(principals), membership.principal_id, membership.status == "active")
    for grant in state.role_grants:
        active = grant.status == "active"
        # Grantor is historical attribution, like created_by. Deprovisioning
        # must not require rewriting every grant that person once issued.
        require(dict(principals), grant.granted_by_principal_id, False)
        if isinstance(grant.subject, PrincipalSubject):
            require(dict(principals), grant.subject.principal_id, active)
            principal = principals[grant.subject.principal_id]
            if (isinstance(principal, ServiceAccount)) != (grant.role == "serviceAccount"):
                raise IntegrityViolation("Invalid principal role.")
        elif grant.role == "serviceAccount":
            raise IntegrityViolation("Service account grants must name a principal.")
        else:
            require(dict(teams), grant.subject.team_id, active)
        scope = grant.scope
        if not isinstance(scope, OrganizationScope):
            require(dict(projects), scope.project_id, active)
        if scope.kind in ("service", "serviceEnvironment"):
            service_id = scope.service_id
            require(dict(services), service_id, active)
            if services[service_id].project_id != scope.project_id:
                raise IntegrityViolation("Invalid ancestry.")
        if scope.kind in ("environment", "serviceEnvironment"):
            environment_id = scope.environment_id
            require(dict(environments), environment_id, active)
            if environments[environment_id].project_id != scope.project_id:
                raise IntegrityViolation("Invalid ancestry.")
        if scope.kind == "serviceEnvironment" and not any(
            binding.service_id == scope.service_id
            and binding.environment_id == scope.environment_id
            and (not active or binding.status == "active")
            for binding in state.service_environments
        ):
            raise IntegrityViolation("Invalid service environment binding.")


def validate_transition(before: IdentityContract, after: IdentityContract, now: datetime) -> None:
    """Lifecycle/ancestry edits cannot silently reparent or remove the last admin.

    Grant delegation/authentication is a separate prerequisite. Call only under
    a transactional authority fence; no HTTP mutation uses this foundation yet.
    """
    if now.tzinfo is None:
        raise IntegrityViolation("Invalid evaluation time.")
    validate_identity(before)
    validate_identity(after)
    if before.organization.id != after.organization.id:
        raise IntegrityViolation("Invalid tenant transition.")
    if before != after:
        if (
            after.organization.revision != before.organization.revision + 1
            or after.organization.authz_revision != before.organization.authz_revision + 1
            or after.organization.created_at != before.organization.created_at
            or after.organization.created_by_principal_id
            != before.organization.created_by_principal_id
            or after.organization.updated_at < before.organization.updated_at
            or before.organization.status == "archived"
        ):
            raise IntegrityViolation("Invalid authority fence transition.")
    for old_group, new_group in zip(
        (
            before.teams,
            before.projects,
            before.services,
            before.environments,
            before.service_environments,
            before.principals,
            before.team_memberships,
            before.role_grants,
        ),
        (
            after.teams,
            after.projects,
            after.services,
            after.environments,
            after.service_environments,
            after.principals,
            after.team_memberships,
            after.role_grants,
        ),
        strict=True,
    ):
        current = {item.id: item for item in new_group}
        for old in old_group:
            new = current.get(old.id)
            if new is None:
                raise IntegrityViolation("Archive records instead of deleting them.")
            for field in (
                "tenant_id",
                "project_id",
                "service_id",
                "environment_id",
                "account_id",
                "team_id",
                "principal_id",
                "subject",
                "scope",
                "role",
                "role_version",
                "action_allowlist",
                "issuer",
                "audience",
                "credential_reference_id",
                "created_at",
                "created_by_principal_id",
                "granted_by_principal_id",
            ):
                if getattr(old, field, None) != getattr(new, field, None):
                    raise IntegrityViolation("Immutable identity or authority changed.")
            if old.status == "archived" and new != old:
                raise IntegrityViolation("Archived identity cannot be reused.")
            if (
                isinstance(old, (HumanPrincipal, ServiceAccount))
                and isinstance(new, (HumanPrincipal, ServiceAccount))
                and new.authz_revision < old.authz_revision
            ):
                raise IntegrityViolation("Authority revision cannot decrease.")
            if new != old and (new.revision != old.revision + 1 or new.updated_at < old.updated_at):
                raise IntegrityViolation("Invalid revision transition.")
    # Team administrators count only while team, membership and human are active.
    # Service accounts cannot satisfy the last-human-administrator invariant.
    humans = {
        p.id for p in after.principals if isinstance(p, HumanPrincipal) and p.status == "active"
    }
    teams = {t.id for t in after.teams if t.status == "active"}
    for grant in after.role_grants:
        if (
            grant.status != "active"
            or grant.expires_at <= now
            or grant.role != "tenantAdministrator"
            or grant.scope.kind != "organization"
        ):
            continue
        if isinstance(grant.subject, PrincipalSubject) and grant.subject.principal_id in humans:
            return
        if (
            isinstance(grant.subject, TeamSubject)
            and grant.subject.team_id in teams
            and any(
                m.status == "active"
                and m.team_id == grant.subject.team_id
                and m.principal_id in humans
                for m in after.team_memberships
            )
        ):
            return
    raise IntegrityViolation("An active human tenant administrator is required.")
