# Identity and authorization foundation

`shipsense-domain` is shared Python code for the FastAPI API and workers. It contains strict, immutable Pydantic contracts, referential/lifecycle validation, an exact-scope role matrix and deny-before-fetch authorization interfaces. It has no credentials, database clients, provider effects, HTTP routes or process-memory production store.

Canonical entity schemas are published in FastAPI OpenAPI components and generated TypeScript. `IdentityContract` describes one internal authoritative tenant snapshot for validation; it is **not** a directory response or browser input. Global account/email/provider binding is deferred to the separately validated authentication implementation under Decision 0009. Identity records have no provider provenance; that is inapplicable until actual provider evidence exists.

## Entities and lifecycle

Organization is the tenant root (`id == tenantId`). Projects belong to a tenant and owner team; services and environments belong to a project. A service/environment relationship is explicit. Teams have a tenant principal owner, and memberships bind that tenant's principals. Human principals reference canonical account IDs. Service accounts have an owner team, purpose, issuer/subject/audience, opaque credential reference and expiry; no secret belongs in these contracts. Creator and ownership references are tenant local.

Names are bounded display text with no controls or surrounding whitespace. Case-folded names are unique per tenant for teams/projects and per project for services/environments; archived names remain reserved. This rule does not define account email normalization. IDs and ancestry are immutable. Updates require the next record revision and a nondecreasing timestamp. Any identity change advances the organization revision and authorization fence. Archived records cannot be reused/deleted; grants are revoked and replaced to change scope/role. Active relationships require active parents. Suspending/deprovisioning a principal therefore requires its active ownership/membership/grant relationships to be reassigned or revoked in the same transaction.

`validate_transition` also requires a remaining active human tenant administrator, through a direct organization grant or active team membership, at the supplied trusted server time. It is a validator, **not a transaction or authorization check**. It cannot prevent concurrent last-administrator removal without a persistence adapter's authoritative fence. Initial bootstrap, grant delegation, migrations/indexes and real MongoDB transactions are unavailable pending their explicit implementation and authorized non-production write proof. Never use unvalidated `model_copy` for external input.

## Role matrix (`p02-exact-v1`)

| Role                 | Capability requests at the exact granted scope                                                         |
| -------------------- | ------------------------------------------------------------------------------------------------------ |
| Reader               | Metadata and evidence reads                                                                            |
| Developer            | Reader plus proposals and bounded operation requests                                                   |
| Operator             | Developer plus investigations                                                                          |
| Security reviewer    | Security and scoped audit reads                                                                        |
| Approver             | Request approval evaluation                                                                            |
| Tenant administrator | Identity administration                                                                                |
| Audit reader         | Scoped audit reads                                                                                     |
| Service account      | Explicit allowlist of metadata/evidence reads, proposals, investigations or bounded operation requests |

There is no scope inheritance in this foundation. An organization/project/service grant does not expand into another scope or environment; production access requires its own exact environment scope. Administrator does not imply operational authority. Human grants cannot be applied to service accounts; service accounts cannot administer identities or approve. Team membership and grants are resolved from current state, never caller headers. Unknown roles/actions and expired/inactive/mismatched authority deny. Approval capability is **not** policy eligibility, step-up, separation-of-duties clearance or effect permission; P02.4 must implement those gates. No action here executes a provider call.

`PrincipalContext` is an internal Python value, constructed only after an actual credential resolver validates the caller. It is not published in OpenAPI or parsed from HTTP/job/model payloads. No credential resolver exists in this slice. `AuthorityStore` must load a validated, tenant-filtered authoritative snapshot on every operation. `AuthorizationService` checks current membership, principal and tenant authorization revisions, expiry, active ancestry and exact grants. Foreign scope is rejected before authority lookup. An append-only decision receipt must succeed before a protected retrieval is invoked; dependency/audit exceptions fail closed. HTTP adapters must map hidden/missing to the same safe envelope and unavailability to 503, without returning raw exceptions.

The `ScopedReader` contract requires the complete scope in the storage query. It must never fetch a global object and filter afterward. Production adapters must keep permission checking, retrieval and authority fencing coherent; this pure evaluator does not solve concurrent revocation by itself. The initial metadata helper illustrates the ordering only. Collections/counts/search/cursors, queue/callback/tool adapters and redaction need their own implemented proof before P02.3 acceptance.

## Persistence and audit boundary

`IdentityUnitOfWork` specifies current delegation checks, revision comparison, one authoritative fence, tenant/principal/action-bound idempotency, and atomic state/result/audit persistence. It has no implementation yet. `AuditWriter` exposes append only; the test collector is synthetic and proves ordering/failure behavior, not durability or tamper resistance. Production audit records, denied-scope sanitization, correlation streams, audit pagination, migrations, restart/race proof and private archive design remain P02.5/P03 work. No update/delete/export endpoint exists.

Run `uv run --frozen --package shipsense-api python -m unittest discover -s packages/domain/tests -v` from the repository root, or use `npm run test:unit`. Tests use two environment scopes and foreign-tenant fixtures, including invalid ancestry/ownership, duplicate identities, last administrator removal, expired/team grants, current authority changes, deny-before-fetch and audit outages. They do not prove Google/GitHub/password authentication, real storage or browser administration.
