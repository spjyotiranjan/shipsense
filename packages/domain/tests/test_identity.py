"""Synthetic domain tests: no real authentication, persistence or provider proof."""

import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from pydantic import TypeAdapter, ValidationError
from shipsense_domain.authorization import (
    ROLE_CAPABILITIES,
    AuthorizationService,
    HiddenResource,
    PrincipalContext,
)
from shipsense_domain.integrity import IntegrityViolation, validate_identity, validate_transition
from shipsense_domain.models import IdentityContract, Organization, ResourceScope, RoleGrant

NOW = datetime(2026, 11, 12, tzinfo=UTC)
TENANT, HUMAN, TEAM, PROJECT, SERVICE, DEV, PROD = [UUID(int=i) for i in range(1, 8)]


def record(identity, **fields):
    return dict(
        id=identity,
        tenantId=TENANT,
        schemaVersion=1,
        revision=1,
        status="active",
        createdAt=NOW,
        updatedAt=NOW,
        createdByPrincipalId=HUMAN,
        **fields,
    )


def scope(environment=DEV):
    return TypeAdapter(ResourceScope).validate_python(
        dict(
            kind="serviceEnvironment",
            tenantId=TENANT,
            projectId=PROJECT,
            serviceId=SERVICE,
            environmentId=environment,
        )
    )


def grant(identity=20, **fields):
    return (
        record(
            UUID(int=identity),
            subject=dict(kind="principal", principalId=HUMAN),
            role="reader",
            scope=scope().model_dump(by_alias=True),
            grantedByPrincipalId=HUMAN,
            expiresAt=NOW + timedelta(hours=1),
        )
        | fields
    )


def fixture(**fields):
    data = (
        dict(
            organization=record(TENANT, name="Example", authzRevision=1),
            teams=[record(TEAM, name="Platform", ownerPrincipalId=HUMAN)],
            projects=[record(PROJECT, name="Shop", ownerTeamId=TEAM)],
            services=[record(SERVICE, projectId=PROJECT, name="Checkout", ownerTeamId=TEAM)],
            environments=[
                record(DEV, projectId=PROJECT, name="Dev", classification="nonproduction"),
                record(PROD, projectId=PROJECT, name="Prod", classification="production"),
            ],
            serviceEnvironments=[
                record(UUID(int=8), projectId=PROJECT, serviceId=SERVICE, environmentId=DEV),
                record(UUID(int=9), projectId=PROJECT, serviceId=SERVICE, environmentId=PROD),
            ],
            principals=[record(HUMAN, kind="human", accountId=UUID(int=10), authzRevision=1)],
            teamMemberships=[],
            roleGrants=[
                grant(),
                grant(
                    21, role="tenantAdministrator", scope=dict(kind="organization", tenantId=TENANT)
                ),
            ],
        )
        | fields
    )
    return IdentityContract.model_validate(data)


class Authority:
    def __init__(self, state):
        self.state = state
        self.calls = 0

    def current(self, context):
        self.calls += 1
        return self.state


class Audit:
    def __init__(self):
        self.events = []
        self.failed = False

    def append_decision(self, decision):
        if self.failed:
            raise RuntimeError("AUDIT_UNAVAILABLE")
        self.events.append(decision)


class Reader:
    def __init__(self):
        self.calls = []

    def metadata(self, requested_scope, object_id):
        self.calls.append((requested_scope, object_id))
        return {"name": "Permitted"} if object_id == SERVICE else None


class IdentityTests(unittest.TestCase):
    def test_complete_snapshot_round_trip_and_normalized_utc(self):
        state = fixture()
        validate_identity(state)
        validate_transition(state, state, NOW)
        self.assertEqual(IdentityContract.model_validate_json(state.model_dump_json()), state)
        data = state.organization.model_dump(by_alias=True)
        data["createdAt"] = "2026-11-12T05:30:00+05:30"
        self.assertEqual(Organization.model_validate(data).created_at, NOW)

    def test_strict_unknown_bounds_revision_time_and_root(self):
        valid = fixture().organization.model_dump(by_alias=True)
        for override in (
            {"role": "admin"},
            {"revision": True},
            {"schemaVersion": True},
            {"revision": "1"},
            {"revision": 0},
            {"name": " "},
            {"name": "x" * 121},
            {"name": "bad\nname"},
            {"name": " padded"},
            {"createdAt": "2026-11-12T00:00:00"},
            {"updatedAt": NOW - timedelta(seconds=1)},
            {"tenantId": uuid4()},
            {"status": "deleted"},
        ):
            with self.subTest(override=override), self.assertRaises(ValidationError):
                Organization.model_validate(valid | override)

    def test_scope_union_rejects_wildcards_extra_and_invalid_ids(self):
        base = scope().model_dump(by_alias=True)
        for override in (
            {"tenantId": None},
            {"environmentId": None},
            {"projectId": "*"},
            {"kind": "all"},
            {"role": "reader"},
        ):
            with self.subTest(override=override), self.assertRaises(ValidationError):
                TypeAdapter(ResourceScope).validate_python(base | override)

    def test_duplicate_ids_names_memberships_and_foreign_ownership(self):
        data = fixture().model_dump(by_alias=True)
        for update in (
            {"teams": [data["teams"][0], data["teams"][0]]},
            {"teams": [*data["teams"], record(uuid4(), name="PLATFORM", ownerPrincipalId=HUMAN)]},
            {"services": [data["services"][0] | {"ownerTeamId": uuid4()}]},
            {"services": [data["services"][0] | {"tenantId": uuid4()}]},
            {"services": [data["services"][0] | {"projectId": uuid4()}]},
            {"environments": [data["environments"][0] | {"status": "archived"}]},
            {"principals": [data["principals"][0] | {"status": "suspended"}]},
            {
                "teamMemberships": [
                    record(uuid4(), teamId=TEAM, principalId=HUMAN),
                    record(uuid4(), teamId=TEAM, principalId=HUMAN),
                ]
            },
        ):
            with self.subTest(update=update), self.assertRaises(IntegrityViolation):
                validate_identity(IdentityContract.model_validate(data | update))

    def test_wrong_project_service_environment_binding_and_grant(self):
        data = fixture().model_dump(by_alias=True)
        other = record(uuid4(), name="Other", ownerTeamId=TEAM)
        data["projects"] = [*data["projects"], other]
        for update in (
            {"services": [data["services"][0] | {"projectId": other["id"]}]},
            {
                "roleGrants": [
                    grant(scope=scope().model_dump(by_alias=True) | {"projectId": other["id"]})
                ]
            },
            {"serviceEnvironments": []},
        ):
            with self.subTest(update=update), self.assertRaises(IntegrityViolation):
                validate_identity(IdentityContract.model_validate(data | update))

    def test_deprovisioned_grantor_remains_immutable_historical_attribution(self):
        data = fixture().model_dump(by_alias=True)
        former = UUID(int=40)
        data["principals"] = [
            *data["principals"],
            record(former, kind="human", accountId=UUID(int=41), authzRevision=1)
            | {"status": "suspended"},
        ]
        data["roleGrants"] = [g | {"grantedByPrincipalId": former} for g in data["roleGrants"]]
        before = IdentityContract.model_validate(data)
        validate_identity(before)
        data["organization"].update(revision=2, authzRevision=2)
        data["roleGrants"][0].update(grantedByPrincipalId=HUMAN, revision=2)
        with self.assertRaises(IntegrityViolation):
            validate_transition(before, IdentityContract.model_validate(data), NOW)

    def test_grant_validation_and_service_account_limits(self):
        for update in (
            {"tenantId": uuid4()},
            {"expiresAt": NOW},
            {"roleVersion": "unknown"},
            {"actionAllowlist": ["identity.manage"]},
            {"role": "serviceAccount", "actionAllowlist": []},
            {"role": "serviceAccount", "actionAllowlist": ["approval.decide"]},
            {"role": "serviceAccount", "actionAllowlist": ["metadata.read", "metadata.read"]},
        ):
            with self.subTest(update=update), self.assertRaises(ValidationError):
                RoleGrant.model_validate(grant() | update)
        with self.assertRaises(IntegrityViolation):
            validate_identity(
                fixture(
                    roleGrants=[grant(role="serviceAccount", actionAllowlist=["metadata.read"])]
                )
            )

    def test_transition_requires_fence_revision_and_preserves_ancestry(self):
        before = fixture()
        data = before.model_dump(by_alias=True)
        changed = data | {
            "organization": data["organization"] | {"revision": 2, "authzRevision": 2},
            "services": [data["services"][0] | {"name": "Checkout v2", "revision": 2}],
        }
        validate_transition(before, IdentityContract.model_validate(changed), NOW)
        for update in (
            {"organization": data["organization"]},
            {"services": [changed["services"][0] | {"revision": 1}]},
            {"services": []},
            {
                "roleGrants": [
                    g | {"scope": dict(kind="organization", tenantId=TENANT), "revision": 2}
                    for g in data["roleGrants"]
                ]
            },
        ):
            with self.subTest(update=update), self.assertRaises(IntegrityViolation):
                validate_transition(before, IdentityContract.model_validate(changed | update), NOW)

    def test_last_admin_revoke_expiry_and_team_membership(self):
        before = fixture()
        data = before.model_dump(by_alias=True)
        data["organization"].update(revision=2, authzRevision=2)
        data["roleGrants"][1].update(status="archived", revision=2)
        with self.assertRaises(IntegrityViolation):
            validate_transition(before, IdentityContract.model_validate(data), NOW)
        with self.assertRaises(IntegrityViolation):
            validate_transition(before, before, NOW + timedelta(hours=1))
        data = before.model_dump(by_alias=True)
        data["roleGrants"][1]["subject"] = dict(kind="team", teamId=TEAM)
        data["teamMemberships"] = [record(uuid4(), teamId=TEAM, principalId=HUMAN)]
        state = IdentityContract.model_validate(data)
        validate_transition(state, state, NOW)
        data["organization"].update(revision=2, authzRevision=2)
        data["teamMemberships"][0].update(status="archived", revision=2)
        with self.assertRaises(IntegrityViolation):
            validate_transition(state, IdentityContract.model_validate(data), NOW)


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.authority = Authority(fixture())
        self.audit = Audit()
        self.reader = Reader()
        self.service = AuthorizationService(self.authority, self.audit)
        self.context = PrincipalContext(HUMAN, TENANT, 1, 1, NOW + timedelta(minutes=5))
        self.correlation = uuid4()

    def read(self, context=None, requested_scope=None, object_id=SERVICE):
        return self.service.read_metadata(
            context or self.context,
            requested_scope or scope(),
            object_id,
            self.reader,
            NOW,
            self.correlation,
        )

    def test_authorized_read_exact_query_and_audit(self):
        self.assertEqual(self.read(), {"name": "Permitted"})
        self.assertEqual(self.reader.calls, [(scope(), SERVICE)])
        self.assertEqual(len(self.audit.events), 1)
        self.assertTrue(self.audit.events[0].allowed)
        self.assertEqual(self.audit.events[0].correlation_id, self.correlation)

    def test_cross_tenant_denies_before_authority_or_protected_fetch(self):
        foreign = scope().model_copy(update={"tenant_id": uuid4()})
        with self.assertRaises(HiddenResource):
            self.read(requested_scope=foreign)
        self.assertEqual(self.authority.calls, 0)
        self.assertEqual(self.reader.calls, [])

    def test_environment_project_ancestry_and_nonexistent_share_denial(self):
        for requested in (
            scope(PROD),
            scope(uuid4()),
            scope().model_copy(update={"project_id": uuid4()}),
        ):
            with self.assertRaises(HiddenResource) as error:
                self.read(requested_scope=requested)
            self.assertEqual(str(error.exception), "")
        self.assertEqual(self.reader.calls, [])
        self.assertEqual({e.reason for e in self.audit.events}, {"not_found"})

    def test_fresh_resolve_revocation_and_expiry_deny_later_read(self):
        self.read()
        self.reader.calls.clear()
        data = fixture().model_dump(by_alias=True)
        for update in ({"status": "suspended"}, {"authzRevision": 2}):
            self.authority.state = IdentityContract.model_validate(
                data | {"principals": [data["principals"][0] | update]}
            )
            with self.assertRaises(HiddenResource):
                self.read()
        for ctx in (
            replace(self.context, expires_at=NOW),
            replace(self.context, tenant_authz_revision=2),
            replace(self.context, principal_id=uuid4()),
        ):
            with self.assertRaises(HiddenResource):
                self.read(context=ctx)
        self.assertEqual(self.reader.calls, [])

    def test_role_expiry_team_removal_and_no_implicit_parent_expansion(self):
        data = fixture().model_dump(by_alias=True)
        for new_grant in (
            grant(expiresAt=NOW - timedelta(seconds=1), createdAt=NOW - timedelta(hours=1)),
            grant(scope=dict(kind="organization", tenantId=TENANT)),
            grant(subject=dict(kind="team", teamId=TEAM)),
            grant(status="archived"),
        ):
            self.authority.state = IdentityContract.model_validate(
                data | {"roleGrants": [new_grant]}
            )
            with self.assertRaises(HiddenResource):
                self.read()
        self.assertEqual(self.reader.calls, [])

    def test_tenant_administrator_has_no_operational_or_approval_privilege(self):
        self.authority.state = fixture(roleGrants=[grant(role="tenantAdministrator")])
        for action in ("metadata.read", "approval.decide", "operation.request"):
            result = self.service.evaluate(self.context, action, scope(), NOW, self.correlation)
            self.assertFalse(result.allowed)
        self.assertEqual(ROLE_CAPABILITIES["tenantAdministrator"], {"identity.manage"})

    def test_active_team_membership_and_revocation_are_resolved_each_time(self):
        data = fixture().model_dump(by_alias=True)
        data["roleGrants"] = [grant(subject=dict(kind="team", teamId=TEAM))]
        data["teamMemberships"] = [record(uuid4(), teamId=TEAM, principalId=HUMAN)]
        self.authority.state = IdentityContract.model_validate(data)
        validate_identity(self.authority.state)
        self.read()
        self.reader.calls.clear()
        data["teamMemberships"][0]["status"] = "archived"
        self.authority.state = IdentityContract.model_validate(data)
        with self.assertRaises(HiddenResource):
            self.read()
        self.assertEqual(self.reader.calls, [])

    def test_service_account_explicit_read_only_and_credential_expiry(self):
        identity = UUID(int=30)
        data = fixture().model_dump(by_alias=True)
        machine = record(
            identity,
            kind="serviceAccount",
            ownerTeamId=TEAM,
            purpose="Read metadata",
            issuer="synthetic",
            subject="worker",
            audience="synthetic-api",
            credentialReferenceId=uuid4(),
            expiresAt=NOW + timedelta(minutes=1),
            authzRevision=1,
        )
        data["principals"] = [*data["principals"], machine]
        data["roleGrants"] = [
            grant(
                subject=dict(kind="principal", principalId=identity),
                role="serviceAccount",
                actionAllowlist=["metadata.read"],
            )
        ]
        self.authority.state = IdentityContract.model_validate(data)
        validate_identity(self.authority.state)
        ctx = replace(self.context, principal_id=identity)
        self.assertEqual(self.read(context=ctx), {"name": "Permitted"})
        for action in ("identity.manage", "approval.decide", "operation.request"):
            self.assertFalse(
                self.service.evaluate(ctx, action, scope(), NOW, self.correlation).allowed
            )
        self.assertFalse(
            self.service.evaluate(
                ctx, "metadata.read", scope(), NOW + timedelta(minutes=1), self.correlation
            ).allowed
        )

    def test_audit_or_authority_outage_never_releases_protected_data(self):
        self.audit.failed = True
        with self.assertRaisesRegex(RuntimeError, "AUDIT_UNAVAILABLE"):
            self.read()
        self.assertEqual(self.reader.calls, [])
        self.audit.failed = False

        def unavailable(context):
            raise RuntimeError("AUTHORITY_UNAVAILABLE")

        self.authority.current = unavailable
        with self.assertRaisesRegex(RuntimeError, "AUTHORITY_UNAVAILABLE"):
            self.read()
        self.assertEqual(self.reader.calls, [])

    def test_missing_and_hidden_objects_have_no_details(self):
        messages = []
        for requested, identity in ((scope(), uuid4()), (scope(PROD), SERVICE)):
            with self.assertRaises(HiddenResource) as error:
                self.read(requested_scope=requested, object_id=identity)
            messages.append(str(error.exception))
        self.assertEqual(messages, ["", ""])


if __name__ == "__main__":
    unittest.main()
