"""Build the initial tenant state for an explicitly selected administrator."""

from datetime import datetime
from uuid import UUID

from shipsense_domain.account_matching import AccountDirectory, ProviderSubject
from shipsense_domain.integrity import IntegrityViolation, validate_transition
from shipsense_domain.models import (
    HumanPrincipal,
    IdentityContract,
    Organization,
    OrganizationScope,
    PrincipalSubject,
    RoleGrant,
)


def build_initial_tenant(
    directory: AccountDirectory,
    *,
    administrator_subject: ProviderSubject,
    administrator_account_id: UUID,
    tenant_id: UUID,
    principal_id: UUID,
    grant_id: UUID,
    name: str,
    now: datetime,
    grant_expires_at: datetime,
) -> IdentityContract:
    """Prepare a revision-one tenant under an operator-selected exact binding.

    A caller must resolve and fence the binding and prove that the tenant is
    absent in the same unit of work that commits this state and its audit
    receipt. This function neither authenticates the operator nor persists.
    """
    account = directory.by_subject(administrator_subject)
    if account is None or account.status != "active" or account.id != administrator_account_id:
        raise IntegrityViolation("Initial administrator binding unavailable.")

    organization = Organization(
        id=tenant_id,
        tenant_id=tenant_id,
        created_by_principal_id=principal_id,
        revision=1,
        authz_revision=1,
        status="active",
        created_at=now,
        updated_at=now,
        name=name,
    )
    administrator = HumanPrincipal(
        id=principal_id,
        tenant_id=tenant_id,
        created_by_principal_id=principal_id,
        revision=1,
        authz_revision=1,
        status="active",
        created_at=now,
        updated_at=now,
        account_id=account.id,
    )
    grant = RoleGrant(
        id=grant_id,
        tenant_id=tenant_id,
        created_by_principal_id=principal_id,
        revision=1,
        status="active",
        created_at=now,
        updated_at=now,
        subject=PrincipalSubject(principal_id=principal_id),
        role="tenantAdministrator",
        scope=OrganizationScope(tenant_id=tenant_id),
        expires_at=grant_expires_at,
        granted_by_principal_id=principal_id,
    )
    state = IdentityContract(
        organization=organization,
        teams=(),
        projects=(),
        services=(),
        environments=(),
        service_environments=(),
        principals=(administrator,),
        team_memberships=(),
        role_grants=(grant,),
    )
    validate_transition(state, state, now)
    return state
