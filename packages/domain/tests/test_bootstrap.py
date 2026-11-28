import unittest
from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import ValidationError
from shipsense_domain.account_matching import DirectoryAccount, ProviderSubject
from shipsense_domain.bootstrap import build_initial_tenant
from shipsense_domain.integrity import IntegrityViolation
from shipsense_domain.models import OrganizationScope, PrincipalSubject

NOW = datetime(2026, 11, 28, tzinfo=UTC)
ACCOUNT, TENANT, PRINCIPAL, GRANT = (UUID(int=value) for value in range(1, 5))
SUBJECT = ProviderSubject("github", "operator-selected-subject")


class Directory:
    def __init__(self, account: DirectoryAccount | None) -> None:
        self.account = account

    def by_subject(self, subject: ProviderSubject) -> DirectoryAccount | None:
        return self.account if subject == SUBJECT else None

    def by_email_key(self, key: str) -> DirectoryAccount | None:
        raise AssertionError("Bootstrap must not resolve an administrator by email.")


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.directory = Directory(DirectoryAccount(ACCOUNT, "operator@example.com", "active"))
        self.parameters = {
            "administrator_subject": SUBJECT,
            "administrator_account_id": ACCOUNT,
            "tenant_id": TENANT,
            "principal_id": PRINCIPAL,
            "grant_id": GRANT,
            "name": "Example",
            "now": NOW,
            "grant_expires_at": NOW + timedelta(hours=1),
        }

    def test_explicit_binding_yields_one_exact_organization_grant(self):
        state = build_initial_tenant(self.directory, **self.parameters)
        self.assertEqual(state.organization.id, TENANT)
        self.assertEqual(state.organization.authz_revision, 1)
        self.assertEqual(state.principals[0].id, PRINCIPAL)
        self.assertEqual(state.principals[0].account_id, ACCOUNT)
        (grant,) = state.role_grants
        self.assertEqual(grant.role, "tenantAdministrator")
        self.assertEqual(grant.scope, OrganizationScope(tenant_id=TENANT))
        self.assertEqual(grant.subject, PrincipalSubject(principal_id=PRINCIPAL))
        self.assertEqual(grant.granted_by_principal_id, PRINCIPAL)
        self.assertEqual(state.projects, ())

    def test_missing_inactive_or_reassigned_binding_denies(self):
        for account in (
            None,
            DirectoryAccount(ACCOUNT, "operator@example.com", "suspended"),
            DirectoryAccount(UUID(int=99), "operator@example.com", "active"),
        ):
            with (
                self.subTest(account=account),
                self.assertRaisesRegex(IntegrityViolation, "binding unavailable"),
            ):
                build_initial_tenant(Directory(account), **self.parameters)

    def test_provider_must_match_exactly(self):
        self.parameters["administrator_subject"] = ProviderSubject("google", SUBJECT.subject)
        with self.assertRaises(IntegrityViolation):
            build_initial_tenant(self.directory, **self.parameters)

    def test_duplicate_ids_and_expired_initial_grant_deny(self):
        with self.assertRaises(IntegrityViolation):
            build_initial_tenant(self.directory, **(self.parameters | {"grant_id": PRINCIPAL}))
        with self.assertRaises(ValidationError):
            build_initial_tenant(self.directory, **(self.parameters | {"grant_expires_at": NOW}))
