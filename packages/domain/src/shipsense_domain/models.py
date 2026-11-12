"""Strict identity records and explicit scopes for the P02 foundation.

These are domain contracts, not authenticated HTTP inputs. Identity resolution
and transactional persistence must validate references before accepting writes.
"""

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictInt, field_validator
from pydantic.alias_generators import to_camel
from pydantic.functional_validators import AfterValidator


def utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


def display_name(value: str) -> str:
    if value != value.strip() or any(not character.isprintable() for character in value):
        raise ValueError("Invalid display name.")
    return value


Timestamp = Annotated[AwareDatetime, AfterValidator(utc)]
Revision = Annotated[StrictInt, Field(ge=1)]
Name = Annotated[
    str, Field(strict=True, min_length=1, max_length=120), AfterValidator(display_name)
]
Status = Literal["active", "suspended", "archived"]
Role = Literal[
    "reader",
    "developer",
    "operator",
    "securityReviewer",
    "approver",
    "tenantAdministrator",
    "auditReader",
    "serviceAccount",
]
Action = Literal[
    "metadata.read",
    "evidence.read",
    "proposal.create",
    "investigation.create",
    "security.read",
    "audit.read",
    "identity.manage",
    "approval.decide",
    "operation.request",
]


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class OrganizationScope(Contract):
    kind: Literal["organization"] = "organization"
    tenant_id: UUID


class ProjectScope(Contract):
    kind: Literal["project"] = "project"
    tenant_id: UUID
    project_id: UUID


class ServiceScope(Contract):
    kind: Literal["service"] = "service"
    tenant_id: UUID
    project_id: UUID
    service_id: UUID


class EnvironmentScope(Contract):
    kind: Literal["environment"] = "environment"
    tenant_id: UUID
    project_id: UUID
    environment_id: UUID


class ServiceEnvironmentScope(Contract):
    kind: Literal["serviceEnvironment"] = "serviceEnvironment"
    tenant_id: UUID
    project_id: UUID
    service_id: UUID
    environment_id: UUID


ResourceScope = Annotated[
    OrganizationScope | ProjectScope | ServiceScope | EnvironmentScope | ServiceEnvironmentScope,
    Field(discriminator="kind"),
]


class Record(Contract):
    id: UUID
    schema_version: Literal[1] = 1
    revision: Revision
    created_at: Timestamp
    updated_at: Timestamp
    created_by_principal_id: UUID
    status: Status

    @field_validator("schema_version", mode="before")
    @classmethod
    def strict_version(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("Invalid schema version.")
        return value

    def model_post_init(self, context: object) -> None:
        if self.updated_at < self.created_at:
            raise ValueError("Invalid record timestamps.")


class TenantRecord(Record):
    tenant_id: UUID


class Organization(TenantRecord):
    name: Name
    authz_revision: Revision

    def model_post_init(self, context: object) -> None:
        super().model_post_init(context)
        if self.tenant_id != self.id:
            raise ValueError("Invalid tenant root.")


class Team(TenantRecord):
    name: Name
    owner_principal_id: UUID


class Project(TenantRecord):
    name: Name
    owner_team_id: UUID


class Service(TenantRecord):
    project_id: UUID
    name: Name
    owner_team_id: UUID


class Environment(TenantRecord):
    project_id: UUID
    name: Name
    classification: Literal["nonproduction", "production"]


class ServiceEnvironment(TenantRecord):
    project_id: UUID
    service_id: UUID
    environment_id: UUID


class HumanPrincipal(TenantRecord):
    kind: Literal["human"] = "human"
    account_id: UUID
    authz_revision: Revision


class ServiceAccount(TenantRecord):
    kind: Literal["serviceAccount"] = "serviceAccount"
    owner_team_id: UUID
    purpose: Name
    issuer: Annotated[str, Field(strict=True, min_length=1, max_length=256)]
    subject: Annotated[str, Field(strict=True, min_length=1, max_length=256)]
    audience: Annotated[str, Field(strict=True, min_length=1, max_length=256)]
    credential_reference_id: UUID
    expires_at: Timestamp
    authz_revision: Revision

    def model_post_init(self, context: object) -> None:
        super().model_post_init(context)
        if self.expires_at <= self.created_at:
            raise ValueError("Invalid credential expiry.")


Principal = Annotated[HumanPrincipal | ServiceAccount, Field(discriminator="kind")]


class TeamMembership(TenantRecord):
    team_id: UUID
    principal_id: UUID


class PrincipalSubject(Contract):
    kind: Literal["principal"] = "principal"
    principal_id: UUID


class TeamSubject(Contract):
    kind: Literal["team"] = "team"
    team_id: UUID


class RoleGrant(TenantRecord):
    subject: Annotated[PrincipalSubject | TeamSubject, Field(discriminator="kind")]
    role: Role
    role_version: Literal["p02-exact-v1"] = "p02-exact-v1"
    scope: ResourceScope
    expires_at: Timestamp
    granted_by_principal_id: UUID
    action_allowlist: tuple[Action, ...] = ()

    def model_post_init(self, context: object) -> None:
        super().model_post_init(context)
        if self.scope.tenant_id != self.tenant_id or self.expires_at <= self.created_at:
            raise ValueError("Invalid grant scope or expiry.")
        if self.role != "serviceAccount" and self.action_allowlist:
            raise ValueError("Allowlist is reserved for service accounts.")
        if self.role == "serviceAccount" and (
            not self.action_allowlist
            or len(set(self.action_allowlist)) != len(self.action_allowlist)
            or set(self.action_allowlist)
            - {
                "metadata.read",
                "evidence.read",
                "proposal.create",
                "investigation.create",
                "operation.request",
            }
        ):
            raise ValueError("Invalid service account allowlist.")


class IdentityContract(Contract):
    """Schema-only aggregate; not a directory response or implemented endpoint."""

    organization: Organization
    teams: tuple[Team, ...]
    projects: tuple[Project, ...]
    services: tuple[Service, ...]
    environments: tuple[Environment, ...]
    service_environments: tuple[ServiceEnvironment, ...]
    principals: tuple[Principal, ...]
    team_memberships: tuple[TeamMembership, ...]
    role_grants: tuple[RoleGrant, ...]
