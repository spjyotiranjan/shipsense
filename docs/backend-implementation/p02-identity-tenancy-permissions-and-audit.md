# P02 backend implementation plan — identity, tenancy, permissions and audit

**Status:** Revised proposal for renewed phase audit, 11 November 2026. This document specifies intended behavior; it is not implementation or acceptance evidence. All new choices below require acceptance before dependent implementation. Include the accepted plans in the first working implementation change.

## Baseline and dependencies

Use [P02 criteria](../../Phases/P02-identity-tenancy-permissions-and-audit.md), [project status](../../PROJECT_STATUS.md), Decisions [0001](../decisions/0001-release-1-scope.md), [0002](../decisions/0002-architecture-baseline.md), [0004](../decisions/0004-phase-planning-and-delivery-standards.md), [0005](../decisions/0005-initial-foundation-toolchain.md), [0006](../decisions/0006-local-quality-toolchain.md), [0007](../decisions/0007-local-foundation-dependencies.md), [0008](../decisions/0008-checkpoint-development-workflow.md) and [0009](../decisions/0009-p02-sign-in-methods.md). The product specification's identity/persona and approval sections (pages 9–11) supply product intent; accepted release decisions control scope. Pair this document with the [web plan](../web-implementation/p02-identity-tenancy-permissions-and-audit.md).

The inspected P01 foundation has public diagnostics in `services/api/src/shipsense_api/main.py`, hosted client lifespan/readiness, canonical OpenAPI, generated TypeScript and a bounded same-process no-effect queue. There are no domain repositories, sessions, permission checks, provider callback handlers or AI tools. Keep `/health/live`, `/health/ready`, `/api/v1/version` and `/foundation` explicitly public and free of tenant data. New domain routes require authentication by default; test the complete route inventory. Preserve current local profile and production refusal.

FastAPI owns domain identity, membership, authorization, policy, sessions and audit. Next.js owns browser-facing session orchestration and presentation. Workers use the same Python authorization package through explicit interfaces; browser or model-supplied identity never establishes authority. MongoDB remains hosted; R2 remains private and is not needed for P02 records. This phase does not authorize cloud provisioning, existing-provider writes, schema/index changes against supplied read-only credentials or production effects. P02 persistence needs separately authorized non-production application/test write access before real write tests; read-only P01 access cannot establish that capability. Continue contract and deterministic tests independently; do not quietly replace required persistence proof with a fake.

## Proposed change grouping and release order

| Group | Implement together | Real prerequisite | Independently recorded proof |
| --- | --- | --- | --- |
| A: P02.1 + P02.5 foundation | Entity/role schemas, scope validator, append-only audit port, atomic unit-of-work contract, minimal scoped administration/read UI | Accepted phase plan; agreed storage-write boundary | P02.1 schemas/lifecycle/matrix; P02.5 initial events, atomicity and read filtering; neither group alone completes P02.5 |
| B: P02.2 + P02.3 | NextAuth Google/GitHub and verified password flows, canonical sessions, service identities, scoped repositories, no-effect worker/callback/tool harnesses, permission UI | A contracts; accepted provider/library/session choices; authorized session storage | P02.2 token/session negatives and real provider and email flows; P02.3 two-tenant/two-environment route and adapter negatives |
| C: P02.4 + P02.5 completion | Versioned policies, approval ledger, step-up, race checks, audit timeline and export design | B authority/revocation; A durable audit/unit of work | P02.4 approval and invalidation matrix; P02.5 correlated reconstruction, failure atomicity, immutability and archive design |

A may expose schemas/read models before login only in tests; no unauthenticated administration endpoint is shipped. First usable administration mutations depend on B. If this makes A too large or unusable, combine A+B rather than introduce a bypass. C remains separate because it adds security-sensitive transition and concurrency behavior. Split a group further if the diff cannot be reviewed as one security boundary; preserve checkpoint-specific evidence in all cases. P03's general event/evidence framework must consume these minimal P02 contracts later, rather than becoming a circular prerequisite for identity.

## P02.1 entity and scope blueprint

Use opaque UUID strings, UTC RFC3339 timestamps and strict extra-field rejection at public inputs. Mongo document IDs are never sufficient query authority. Proposed common stored fields: `id`, `schemaVersion: 1`, `revision: int >= 1`, `createdAt`, `updatedAt`, `status: active|suspended|archived`, `createdByPrincipalId` and `tenantId` for every tenant record. A tenant root uses `tenantId == id`. Global account/provider-subject mapping has no tenant payload and is accessible only through identity resolution, never tenant search.

| Entity | Required domain fields and relationships | Lifecycle/ownership boundary |
| --- | --- | --- |
| Organization | Tenant root, display name, immutable identity, authorization epoch | Organization is the isolation boundary; no implicit cross-organization administrator |
| Project | `tenantId`, name, owner team, revision | Team must belong to same tenant; archive prevents new actions |
| Team / team membership | Tenant-scoped team; principal and membership version | Team grants cannot exceed the containing role grant; removal increments authority version |
| Service | Tenant/project, owner team, name | Minimal identity only; P04 adds catalog/topology |
| Environment | Tenant/project, name, `classification: nonproduction|production` | Service-environment binding explicitly establishes where a service exists; a name such as “dev” is not authority |
| User identity / tenant principal | Global account with unique verified email key and unique provider subjects; separate tenant principal and membership status | No implicit email-based linking or auto-join; deprovisioning removes authority and revokes sessions |
| Service account | Tenant principal, owner team, purpose, issuer subject, audience, credential reference, expiry | Noninteractive; no human approval or step-up privilege; disable/rotation invalidates pending work |
| Role grant | Principal or team, role version, explicit scope, expiry, grantor, revision | A grantor must hold delegable authority for the complete target scope; cannot manufacture wider grants |

Logical roles map to capabilities rather than hard-coded UI personas:

| Role | Default capabilities within an explicit grant | Excluded without a separate grant/policy |
| --- | --- | --- |
| Reader / engineering observer | Read permitted metadata and evidence | Writes, approvals and unrestricted audit |
| Developer | Reader plus propose changes and bounded non-production action requests | Production approval, identity administration |
| Operator / SRE | Investigation and operational proposals in granted service/environments | Policy publication and self-approval |
| Security reviewer | Read permitted security/audit evidence; review explicitly granted security proposals | General environment/operator authority |
| Approver | Approve eligible classes in granted environments | Proposer self-approval; service-account approval |
| Tenant administrator | Manage tenant membership and delegable grants | Implicit production execution, approval bypass or cross-tenant support access |
| Audit reader | Read redacted scoped material-decision timeline | Unrestricted secrets, other tenants, archive deletion |
| Service account | Explicit task/action allowlist | Interactive login, role administration, human approval |

Roles can be combined only through explicit grants. Deny rules, inactive membership, expiry, environment restrictions and separation of duties override allows. No break-glass bypass is implemented in P02; enterprise emergency access remains a later explicit design.

Proposed normalized `ResourceScope` is a tagged union: `organization {tenantId}`; `project {tenantId, projectId}`; `service {tenantId, projectId, serviceId}`; `environment {tenantId, projectId, environmentId}`; `serviceEnvironment {tenantId, projectId, serviceId, environmentId}`. Null never means wildcard. Each action declares the scope kind it accepts. Parent grants expand only through named inheritance rules in the versioned role matrix; production-environment effects always require an explicit environment grant. Validate ancestry with scoped lookups before using a supplied ID. Time-bounded evidence requests add `from`, `to`, `observedAt`, provider identity/version and freshness; identity-only records mark those fields inapplicable rather than fabricating provider provenance.

Use tenant-prefixed unique indexes for names/relationships as appropriate, `(issuer, subject)` for identity mapping, `(tenantId, principalId, status)` for grants and `(tenantId, projectId, serviceId, environmentId, id)` for resource reads. Enforce referential and lifecycle rules in the unit of work; MongoDB has no application foreign keys. Prevent removal of the last active tenant administrator, cross-tenant reparenting and silent reuse of archived identities. Bootstrap an initial tenant administrator through an explicit non-production setup operation with exact issuer subject and audit, never “first login becomes admin.” First migrations create only these necessary collections/indexes, are versioned and idempotent, and never drop user state on rollback; destructive changes require a separate migration plan.

## P02.2 sign-in methods and canonical identity

[Decision 0009](../decisions/0009-p02-sign-in-methods.md) accepts NextAuth for Google, GitHub and email/password; registration collects full name, email and password, and password access requires verified email. It narrows the earlier local-issuer selection: Keycloak/Dex are no longer the proposed sign-in path. Google is OIDC; GitHub is OAuth with authenticated identity/email API checks. No new broker or infrastructure is selected. The details below remain proposals pending phase acceptance and compatibility/security proof.

Next.js runs NextAuth provider handlers and server-only Credentials `authorize`; FastAPI owns accounts, password verification, linking/recovery, canonical sessions, membership and audit. The [Auth.js credentials guide](https://authjs.dev/getting-started/authentication/credentials) leaves persistence and lifecycle logic to the application. [NextAuth v4 Credentials](https://next-auth.js.org/providers/credentials) requires JWT sessions. Validate the exact maintained release against pinned Next.js/React/Node; do not mix v4/v5 examples or silently change libraries. Propose JWT strategy without a default database adapter so library account writes/linking cannot bypass canonical rules. Prove callbacks, logout, safe errors and the session bridge before dependent work.

Proposed credential rules:

| Boundary | Accepted credential and validation | Explicit rejection |
| --- | --- | --- |
| Browser → Next.js | Encrypted NextAuth HttpOnly cookie; Origin/CSRF on mutations; library validation then canonical resolve | Raw role/tenant headers, tokens in browser storage, GET mutations |
| Next.js → FastAPI | BFF service identity with internal audience plus opaque session handle; independent session/user validation | Session handle alone, service identity alone for user-domain actions, caller-supplied user ID |
| Direct human client → FastAPI | No public human bearer issuance in initial P02; protected direct calls fail closed | Google ID token, GitHub token or NextAuth cookie/JWT as API bearer |
| Worker → canonical API | Short-lived workload token plus durable job/delegation ID and exact scope/version | Copied browser token as durable job authority; envelope role claims |
| Provider return → Next.js | One-use provider/purpose-bound transaction, state and supported PKCE/nonce; fixed redirect | Replayed code/state, issuer mix-up, arbitrary return URL |
| Future provider → callback verifier | Connector-specific signature/credential and installation mapping, replay protection, then tenant-scoped ingestion capability | Treating a webhook signature as user or effect authority |

At internal provider exchange require BFF service identity plus a one-use transaction and independently checked proof, never an arbitrary BFF email/profile assertion. Google ID-token validation checks configured signature/issuer/web-client audience/authorized-party as applicable, expiry and transaction nonce; reject `none`, algorithms outside a configured allowlist, ambiguous/duplicate headers or claims, token-selected key URLs and unknown issuers. Use maintained verifiers, bounded rate-limited fixed-origin JWKS refresh and proposed 30-second skew. GitHub tokens are opaque: FastAPI checks fixed GitHub identity/email APIs, not invented JWT claims or introspection. Validate required code/PKCE support against the [current GitHub flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps) and pinned NextAuth release; unsupported required protections block that provider. BFF/workload credential issuance, distinct audiences/scopes, custody and rotation require an accepted scheme; Google/GitHub are not assumed to issue workload authority. Harnesses must reject forged/expired/revoked/wrong-audience credentials under that actual scheme.

API sessions store a hash of a random 256-bit handle, account/auth-method reference, credential/auth epoch, creation/idle/absolute expiry, revocation and revision. Propose absolute cap 15 minutes and idle expiry 10 minutes, no rolling extension beyond the cap, no refresh tokens. The [Auth.js JWT reference](https://authjs.dev/reference/core/jwt) describes encrypted session tokens. Propose that cookie envelope contain only canonical handle/reference and bounded expiry, never provider tokens, roles or authoritative membership. The browser-visible session callback must omit the handle. Every protected BFF request resolves canonical state; JWT validity alone grants nothing. Block an incompatible bridge rather than invent custom JWT cryptography. Retain no provider tokens initially; any subsequently accepted retained bundle needs authenticated encryption and restricted use, keys outside MongoDB (private local development secrets; Azure secret management on later deployment).

Each protected operation rechecks local session/account/epoch/membership. Logout, reset, method changes and deprovisioning revoke canonical authority immediately. Revoke before clearing cookies. If storage is down, clear browser state, fail protected requests closed and disclose that server revocation is unconfirmed; cookie deletion is not proof. Google/GitHub lack the earlier assumed uniform per-operation introspection. Fresh provider proof at every new short session does not establish immediate external disable/revocation detection: a local session may remain valid for its cap, and provider-wide disable semantics still need measurement. Accept provider-specific events/revalidation and maximum lag before claiming that P02.2 criterion; it remains incomplete until demonstrated. Do not claim expiry proves revocation or local logout signs out the provider globally.

### Provider email evidence and normalization

Resolve immutable Google `sub` or GitHub numeric user `id` before email collision lookup; usernames/email may change. Provider email changes never silently change the account key or bind another account. No email/domain/`hd`/organization string grants tenant membership. Existing bindings with insufficient current evidence enter restricted remediation, never a tenant session. Sign-in consent is separate from later connector authority.

| Method | Canonical evidence | Missing or insufficient evidence |
| --- | --- | --- |
| Google | Independently validated token and strict verified-email evidence; Gmail or verified Workspace with `hd` are authoritative mailbox cases | False/missing/malformed verification fails. Third-party email needs a ShipSense mailbox challenge bound to still-valid subject/transaction, even if `email_verified` is true |
| GitHub | Fixed `/user` plus paginated `/user/emails` under exchanged token; exact subject and `verified: true` email. Propose primary verified email and OAuth `user:email` scope | Public profile email may be private/null, with no verification guarantee. Missing scope, API failure, unverified/placeholder/noreply email, ambiguous primary or incomplete pagination gets no session; fix GitHub email then retry |
| Email/password | Active canonical account, verified email key and active Argon2id credential | Pending, disabled, unknown and bad password receive the same safe failure |

These distinctions follow [Google server validation](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token) and [GitHub email API](https://docs.github.com/en/rest/users/emails). Extra challenge/rejected-address policies are proposals, not provider guarantees.

Proposed `emailKeyVersion: 1`: bounded ASCII mailbox up to 254 characters, trim surrounding ASCII space, validate syntax, lowercase local part/domain for a deliberately case-insensitive product key; retain original delivery/display address privately. Reject unsupported internationalized/ambiguous forms. Do not strip plus tags/dots or merge aliases. Accept the local-part case-collision tradeoff explicitly; use the same function for provider, password, linking and recovery. Full name is Unicode display text of 1–120 trimmed characters, rejects controls, escapes on output and never proves identity. Extra profile data is optional later.

### Account schema and uniqueness — P02.1/P02.2

```text
Account = { id: UUID, emailKey: string, emailKeyVersion: 1,
  deliveryEmail: string, fullName: string, status: active|suspended|archived,
  emailVerifiedAt: UTCDateTime, authEpoch: integer, revision: integer }
ProviderBinding = { accountId: UUID, provider: google|github, subject: string,
  observedEmailKey: string, verifiedEvidenceKind: string,
  checkedAt: UTCDateTime, linkedAt: UTCDateTime, revision: integer }
PasswordCredential = { accountId: UUID, argon2idPHC: secret-string,
  credentialVersion: integer, changedAt: UTCDateTime, status: active|disabled }
PendingRegistration = { id: UUID, emailKey: string, deliveryEmail: string,
  fullName: string, pendingArgon2idPHC: secret-string,
  transactionId: UUID, generation: integer, expiresAt: UTCDateTime }
AuthTransaction = { id: UUID, purpose: register|verifyEmail|link|reset|reauth,
  targetAccountId: UUID|null, emailKey: string, providerSubject: string|null,
  browserBindingHash: SHA256, proofHash: SHA256, generation: integer,
  expiresAt: UTCDateTime, consumedAt: UTCDateTime|null, revision: integer }
MailAttempt = { id: UUID, transactionId: UUID, generation: integer,
  state: pending|accepted|delivered|deferred|bounced|failed|unknown,
  providerMessageRef: string|null, attemptNumber: integer, correlationId: UUID }
```

Global auth records contain no tenant directory data and are accessible only through service-authenticated auth operations. Tenant principals reference account ID. Unique indexes on `emailKey`, `(provider, subject)`, `(accountId, provider)` and credential `accountId` are authoritative; propose one binding per provider/account. Pending registration is separate, with bounded retention, and cannot indefinitely reserve an active key. Activation, link, password change, session rotation, idempotency and audit use transactions and revision preconditions. Concurrent social/signup/verify/link winners cannot create duplicate accounts, orphan bindings or wrong-account credentials. Map duplicate-key races to safe outcomes, never raw database errors. Index creation/real race proof awaits authorized non-production writes.

### Registration, verification, password reset and pre-hijack protection

Validate signup fields, hash the password off the async loop with a maintained Python Argon2 library, and atomically create a pending registration plus mail job. Proposed passwords: 15–128 characters and bounded UTF-8 byte length, no composition rules/trim/truncation; allow paste/password managers. Check a local compromised-password list without transmitting passwords. [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) gives an Argon2id floor of 19 MiB, two iterations, parallelism one; benchmark upward with unique random salts and versioned PHC parameters. Rehash on successful login. Never reversible-encrypt or audit passwords. Bound hashing concurrency/body size before expensive work; unknown users perform dummy-hash verification.

Propose 256-bit random tokens stored only as SHA-256 hashes; bind purpose/account/email/generation, with 30-minute verification and 15-minute reset expiry. Server time and atomic unused-state/expiry checks govern use; TTL only cleans up. GET renders a no-store confirmation, never consumes/activates: email scanners cannot activate accounts. A browser-bound POST consumes once. Registration confirmation requires the initiating browser transaction plus re-entry of its pending password; cross-device users restart signup. A victim clicking an attacker-generated link must not activate the attacker's password. Verified social signup colliding with pending signup discards the pending password/proofs, never inherits them. Verification does not auto-login.

Resend requires cooldown, a new generation invalidating older unused proofs, bounded pending lifetime and no changes to active accounts. Reset start always returns generic acceptance. Only existing password credentials receive reset proofs; social-only accounts receive private provider/account-management guidance. Reset cannot add a password to a social-only account. Confirmation requires the reset-start browser binding, one-use proof and new password; atomically increment credential/auth epochs, invalidate all reset proofs/sessions, audit and send security notice. Do not auto-login. Expired/replayed/cross-device links offer a fresh request. [OWASP reset guidance](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html) informs these safeguards; exact durations/binding policies remain proposals. Do not log tokens, URL queries, passwords or email bodies, or expose them through referrers/analytics.

### Same-email sign-in, explicit linking and recovery

Keep `allowDangerousEmailAccountLinking` false/absent. [NextAuth OAuth documentation](https://next-auth.js.org/configuration/providers/oauth) also describes automatic linking when already signed in: that flag alone is insufficient. Without a default adapter, canonical link writes still require explicit intent and proof. Prove ordinary signed-in `signIn` cannot change bindings.

| Situation | Result and safe next step |
| --- | --- |
| Google-only account attempts password | Fixed invalid-sign-in response; show Google/GitHub guidance for every failed password attempt. After Google sign-in, Account → Sign-in methods → Add password requires recent bound-method reauthentication plus new mailbox proof |
| Bound subject returns | Resolve by binding and revalidate current evidence/account state; no email-based account switch |
| New subject matches active email | No auto-merge/session/binding. Generic completion failure with universal sign-in choices; authenticate existing method then explicitly link |
| Unused verified email | Atomic account/binding creation; no tenant auto-join/grant. Empty scope state until explicit membership/bootstrap policy |
| Add Google/GitHub | Active session, fresh existing-method proof, CSRF and one-use link intent bound to account/provider/epoch; independently authenticate new provider, require verified email matching account key and explicit final confirmation |
| Add password / remove method | Add requires recent existing-method proof, mailbox verification and newly chosen password. Remove requires fresh independent retained-method proof; refuse last usable method removal and races. Notify and rotate/revoke sessions |
| Lost provider/all methods | Recover through provider or separately approved high-assurance procedure. P02 offers no admin/email-only override; matching email/support ticket/mailbox control alone cannot restore privileges or attach a method |

No unauthenticated provider-discovery endpoint. Propose universal Google guidance rather than revealing the stored provider set; accept this enumeration tradeoff. Private guidance can name a method after mailbox proof but cannot authorize linking. Social-only users without a functioning provider cannot recover by password reset; accept that limitation or separately design stronger recovery. Email changes/cross-account merges are unavailable in P02. Linked methods preserve one account ID, preventing another method from bypassing separation of duties.

### Email delivery and abuse controls

Propose Twilio **SendGrid Mail Send**, rather than SMS Verify or NextAuth passwordless Email. This interprets the accepted Twilio email requirement; exact service/sender/region/tier remains for acceptance. [Mail Send](https://www.twilio.com/docs/sendgrid/api-reference/mail-send/mail-send) uses a verified sender to send application-generated messages. HTTP acceptance is not delivery or mailbox verification: only consumed application proof activates password access. Planning authorizes no live sends, provisioning or spend.

Use a durable bounded mail outbox/immutable attempts tied to transaction generation, fixed approved origin, escaped templates and server-only least-privilege sending credentials. Custom arguments contain opaque correlation only, no email/name/token. Disable tracking for verification/reset links. Any retry payload containing proof must be authenticated-encrypted, access-restricted and deleted after success/expiry. Timeout is unknown outcome; bounded retry may duplicate email but cannot create additional usable proofs or consume newer generations. Suppression, quota, bounce, auth error and expiry leave registration inactive with safe retry/restart and redacted operational alert. Storage failure prevents successful registration acknowledgement of persisted work; do not claim queued/delivered state without evidence.

Optional delivery telemetry uses [signed SendGrid raw-body events](https://www.twilio.com/docs/sendgrid/for-developers/tracking-events/getting-started-event-webhook-security-features), configured key, bounded timestamp/replay window, payload limits and event deduplication. [Delivered](https://www.twilio.com/docs/sendgrid/for-developers/tracking-events/event) means receiving-server acceptance, not inbox ownership. Telemetry never activates accounts or becomes a login dependency.

Propose shared durable limits: signup/reset/resend three per email key per 15 minutes, 60-second resend cooldown; five password failures per key per 15 minutes with bounded backoff; 30 auth starts per IP per 15 minutes plus global mail/hash budgets. Apply identical buckets to unknown keys, keyed-hash limiter keys, trusted proxy/IP configuration and bounded expiring state. Avoid permanent lockout/attacker-triggered credential changes. 429/cooldowns and timing must not reveal account/method existence. Verify multi-instance/concurrent enforcement. CAPTCHA, if needed later, requires an accessible alternative and separate decision.

## P02.3 authorization and untrusted work

Introduce `PrincipalContext`, `ScopeResolver`, `AuthorizationService`, `ScopedRepository`, `AuditWriter` and `UnitOfWork` interfaces in a shared Python domain package. Keep them independent of the existing diagnostic fixtures. Suggested internal signature:

```python
authorize(principal: PrincipalContext, action: Action,
          scope: ResourceScope, resource_version: str | None,
          purpose: Literal["read", "propose", "approve", "effect"])
# -> Decision(id, allow, safe_reason_code, policy_version,
#             membership_version, evaluated_at, expires_at)
```

Only authenticated resolution constructs `PrincipalContext`; it contains principal kind, canonical account/provider-subject reference, tenant membership/version, session/workload reference and authentication assurance. It is never deserialized directly from an HTTP body or queue message. Decision validity is bounded and effects always reevaluate.

Apply authentication → membership → validated scope ancestry → action permission/policy → scoped repository query → redacted serialization. Pagination/count/search use the same authorized database filter, never post-filtered global results. Counts and suggestions must not reveal denied objects. Opaque cursors bind principal, tenant, query scope and authorization version; changing any invalidates the cursor. Audit endpoints apply the same filtering before pagination. Return indistinguishable 404 responses for a hidden and nonexistent object; 403 is permitted only for an already visible resource and safe action reason. Authentication failures return 401; unavailable authority/audit dependency returns fixed 503, never a permissive fallback. Preserve correlation and no-store headers. Do not return validation errors containing submitted tokens, rejected input or raw database errors.

Every queued job has immutable `jobId`, `delegationId`, initiating principal, exact scope, action, resource/policy version, issued/expiry times, correlation and idempotency key. Those fields describe requested work, not authority. Authenticate the consumer and load current delegation/grants again at dequeue and immediately before any protected retrieval/effect. Deprovisioning, expiry, changed version or a narrower grant denies delayed work. Durable claims/attempts are required before future provider execution; the P01 memory queue cannot supply this guarantee.

Implement a no-effect worker harness, a raw-body signature/replay-verifier contract harness and a tool gateway harness in P02. They exercise the real authorization service, including forbidden retrieval/count/suggestion and malicious envelope arguments, without starting connector ingestion or a model. Unknown/unconfigured callback routes are closed. P05–P07 must add each provider's actual signature format, installation mapping, permission freshness and receipts; P09 must add actual model/tool/checkpoint isolation. P02 proof must name these remaining integration gates.

## API contracts

FastAPI publishes canonical OpenAPI and safe error schemas; generated TypeScript is consumed by Next.js with runtime response validation. These are proposed route families, not implemented endpoints. Choose bounded page sizes (default 25, maximum 100), lengths and UTC ranges in schemas. Mutation bodies reject unknown properties. Expose explicit security requirements for internal service-plus-session access and distinct workload access; direct human bearer routes remain unavailable; no unauthenticated alternative in OpenAPI.

| Contract | Request / response and authority |
| --- | --- |
| `GET /api/v1/me` | Current principal and permitted tenant references only; no global directory |
| `GET /api/v1/tenants/{t}/context` | Authorized projects/services/environments, capabilities and authz revision; empty means no available scope |
| `/api/v1/tenants/{t}/projects`, `/teams`, `/services`, `/environments`, `/principals`, `/role-grants` | Minimal scoped list/create/update/archive contracts; `revision` precondition, delegable administration and audit on mutations |
| Internal provider/password session exchange | BFF credential + one-use transaction + independently checked provider proof or password; returns handle/expiry only to BFF |
| Internal session resolve/revoke | BFF credential + handle; constant safe errors, current-user checks; revoke is idempotent |
| `POST /api/v1/tenants/{t}/policy-evaluations` | Scope, action, candidate/version; returns decision ID, version, safe reasons and requirements; never a reusable execution permit |
| `/api/v1/tenants/{t}/proposals` | Create/read immutable candidate revisions; bound scope/action/digests and expiry |
| `POST .../proposals/{id}/approvals` | Exact candidate/policy/verification versions, expected state revision, decision, reason; human assurance required |
| `GET /api/v1/tenants/{t}/audit-events` | Permission-scoped time/correlation filters and opaque cursor; redacted append-only timeline |

Use `Idempotency-Key` on material mutations, scoped to tenant, principal, route/action and canonical request digest. Same key/different payload returns safe 409; same key/same payload returns the recorded result only after current authorization recheck. Require expected revision through `If-Match` or a single consistent schema precondition; proposed standard is `If-Match` for HTTP and `expectedRevision` internally. State/version mismatch yields 409, expired eligible approval yields 409, missing recent assurance yields a safe `STEP_UP_REQUIRED` response. Document 400/401/403/404/409/422/429/503 and redacted examples, preserving the established error envelope and request ID. All route-specific error codes must be added to canonical schemas, not mapped to generic success in the BFF.

The following schema notation fixes the approval boundary; implement it in canonical Pydantic/OpenAPI, then generate the web types. `UUID`, `UTCDateTime` and `SHA256` mean validated UUID strings, timezone-aware UTC timestamps and lowercase 64-hex digests. A digest is calculated from versioned canonical serialization of the complete binding, not arbitrary client JSON.

```text
MaterialRef = { kind: "sha256", digest: SHA256 }
            | { kind: "notApplicable", reasonCode: string }
            | { kind: "unknown" }
CandidateBinding = {
  schemaVersion: 1, tenantId: UUID, projectId: UUID,
  serviceId: UUID, environmentId: UUID, proposalId: UUID,
  candidateRevision: integer >= 1, action: Action,
  providerTarget: MaterialRef, artifact: MaterialRef,
  baseCommit: MaterialRef, diff: MaterialRef, config: MaterialRef,
  dependencies: MaterialRef, verification: MaterialRef,
  rollback: MaterialRef, policyVersion: string,
  proposerPrincipalId: UUID, expiresAt: UTCDateTime
}
ApprovalInput = {
  candidateDigest: SHA256, candidateRevision: integer >= 1,
  policyVersion: string, verificationDigest: SHA256,
  decision: "approve" | "reject", reason: string[1..2000]
}
ApprovalView = {
  approvalId: UUID, proposalId: UUID, candidateDigest: SHA256,
  candidateRevision: integer >= 1, policyVersion: string,
  approverPrincipalId: UUID, roleVersion: string,
  authzRevision: integer >= 1, assuranceAt: UTCDateTime,
  expiresAt: UTCDateTime, stateRevision: integer >= 1,
  outcome: "approved" | "rejected", correlationId: UUID
}
```

The approver, role, assurance, expiry cap and correlation in the response are server-derived; supplying them in the request is rejected. `If-Match` carries the current proposal state revision. Required verification for approval must be known and match `verificationDigest`; the policy defines which other `notApplicable` values are valid for an action. `unknown` never satisfies an approval requirement. Non-service actions use their own strict scope-specific binding variant rather than omitting required service/environment fields from this variant. On later invalidation retain this immutable approval fact and append an invalidation event; an eligibility read derives `eligible|expired|superseded|revoked|consumed` separately.

## P02.4 policy and exact-version approvals

Implement a deterministic versioned policy evaluator, not an AI decision. A proposal revision binds tenant/project/service/environment, action, target provider object/version where applicable, artifact/base/diff/config/dependency digests, verification manifest, rollback reference, proposer, expiry and policy version. Use explicit `notApplicable` tags for inapplicable identities; unknown evidence/authority is blocking rather than null-as-approved. Persist immutable proposal revisions and approval attempts; only their aggregate state projection changes.

Initially load immutable schema-validated policy bundles from reviewed versioned configuration with a content digest. Unknown actions/default cases deny. Decisions retain bundle version/digest and matched safe rule IDs. Dynamic policy publication and production emergency exceptions are unavailable; adding them later must preserve separate author/reviewer and material-change invalidation. This supplies executable P02 policy decisions without inventing an unrestricted policy editor.

Proposed lifecycle: `draft → pending → approved|rejected|expired|superseded`; cancellation is a separate terminal transition. Approval eligibility requires active independent human approver, explicit action/environment grant, correct role version, recent step-up, unexpired candidate and current policy/verification/material versions. The same global human identity cannot self-approve through another tenant principal or linked account. Service accounts cannot approve. P02's sole executable sensitive demonstration is a synthetic non-production protected operation; provider effects remain unavailable.

Step-up needs a one-use canonical challenge bound to initiating session, exact proposal digest and proposed five-minute freshness. Fresh existing-method reauthentication for account management is distinct from high-assurance sensitive-action step-up. Google/GitHub sign-in and password authentication do not automatically prove MFA, authentication time or sufficient assurance claims. Define and validate a supported factor/assurance profile before enabling sensitive approval; unsupported assurance blocks it. P02.4 needs real supported success/failure proof, never a synthetic claim or checkbox. Persist assurance references/time, never passwords or one-time codes.

Changes to scope/action, artifacts/config/dependencies, provider target, verification, proposer/approver authority, required role, policy or expiry invalidate approval. On consumption recheck user and provider authority, policy, exact versions and expiry; approval is a condition, not authority by itself. Require compare-and-set on aggregate revision and one-time consumption keyed by approval/candidate/effect ID. Concurrent approve/change, approve/revoke, expiry/consume and duplicate submissions must have deterministic winners. Authorization-changing writes and sensitive actions must contend on an authoritative tenant/principal fence in the same unit of work so a stale snapshot cannot approve after revocation. Future remote provider actions require an immutable prepared attempt/outbox and provider idempotency/reconciliation; a database transaction cannot atomically commit a remote effect. P02 does not claim to solve that distributed boundary with an in-memory lock.

## P02.5 audit, durability and tamper-evidence design

Proposed event schema: `eventId`, `schemaVersion`, `tenantId` or an explicitly unscoped authentication-failure partition, validated resource scope, `recordedAt`, `occurredAt`, stream sequence, `actorRef`, `actorKind`, `action`, `outcome`, safe reason, `requestId`, server-established `correlationId`, `causationId`, decision/proposal/approval/attempt IDs, policy/role/resource versions, optional provider object/receipt digest and provenance/freshness. Unauthenticated tenant claims remain untrusted metadata and cannot enter another tenant's visible timeline. Request IDs support tracing but are neither authority nor idempotency keys.

Append registration/verification, password-reset/link attempts, mail outcomes, authentication/revocation, membership/grant changes, sensitive reads, denials, deterministic decisions, approval transitions, protected-operation attempts and simulated receipts. Future provider receipts and observed health are separate event types; neither receipt nor merge implies recovery. Omit raw tokens, secrets, unrestricted source bodies and denied-object names. Enforce bounded metadata allowlists. Corrections append a superseding event; expose no update/delete audit API and give the application audit adapter only insert/read operations. TTL must not silently delete material decisions. Retention/export/privacy requirements need explicit later lifecycle decisions; P02 proposes no indefinite archive guarantee.

Commit a material domain mutation, idempotency result and audit event together using MongoDB transactions where supported and authorized. Validate actual transaction support, unique indexes and read/write concerns on the selected deployment before claiming durability. If unavailable, block persistence acceptance rather than silently splitting writes. For a sensitive read, require its audit write before releasing protected response bytes; writer failure returns 503. Failed attempts append separate outcomes where storage remains available. If audit storage is unavailable, deny the protected operation, emit only a safe operational failure metric/request reference and disclose the unrecorded attempt; never claim complete durable audit during a storage outage.

Order within a correlation stream by atomically allocated sequence and server timestamp, retaining observed provider times separately. Index `(tenantId, correlationId, sequence)`, `(tenantId, recordedAt, eventId)` and scope-specific authorized timeline queries; unique event/idempotency keys prevent duplicate material events. Bound transaction retry/deadline, audit page/range and per-principal request rates. Avoid a single global sequence lock; measure hot-tenant fence contention and p95 latency at the 20–30-user target before enlarging caches or pools.

Tamper evidence/export is a design deliverable here: propose versioned canonical event serialization, per-tenant chain/checkpoint hashes, signed manifests and encrypted permission-filtered exports into private R2 with short-lived access after authorization recheck. Chain rewrites by a privileged database operator remain possible without independently anchored signed checkpoints; application append-only controls are not WORM storage. P03/P18 must settle retention, key custody/rotation, archive anchoring, deletion/legal holds, export consistency and private-object access before enabling archive export. P02 supplies no export/download endpoint or live R2 write.

## Verification and checkpoint exit evidence

These are planned checks, not executed results. Use the existing frozen installs and `npm run quality`, `npm run test:unit`, `npm run build`, `npm run test:smoke`, `npm run contracts:check` and queue diagnostics as applicable; extend meaningful Python/web/contract suites for the new surfaces. Security/shared-schema changes warrant cross-surface regression, actual API and built-web behavior, and route inventory checks. Keep credential-free CI; privately configured integration tests remain separate from secret-free PR execution under Decision 0007. Do not invent a new hosted-verification release system.

| Checkpoint | Required proof at its delivered revision |
| --- | --- |
| P02.1 | Entity/schema and role-matrix review; ownership/lifecycle examples; duplicate identity/name and invalid ancestry tests; last-admin removal and cross-tenant grant denial; migration dry-run/idempotency and explicit write-access limits |
| P02.2 | Exact NextAuth compatibility/session-bridge proof; real Google/GitHub/verified-password login, logout, expiry, canonical revocation/deprovisioning and measured external revocation semantics; forged/wrong issuer/audience/type/algorithm and key rotation/outage negatives for each actual API/BFF/workload scheme (JWKS only where applicable); callback replay and session theft-without-BFF-identity rejection |
| P02.3 | Two tenants, two projects and dev/prod environment fixtures; deny direct ID, collection, pagination, count, search, suggestions, audit and no-effect tool/worker access; compare hidden versus nonexistent errors/body/headers; no forbidden record reaches serializers/logs/prompts; environment tampering, cursor replay and queued revocation cases |
| P02.4 | Independent approver success; self-approval via alternate identity, service-account approval, missing assurance, expired approval and every material-change invalidation; parallel approval/revoke/change/consume and idempotency collision tests; synthetic operation has zero provider effects |
| P02.5 | Reconstruct sensitive read → decision → proposal → independent approval → synthetic attempt → simulated receipt under one correlation; append-only adapter/update denial, duplicate/reordered events, cross-tenant audit denial; injected audit failure rolls back mutation or withholds response; transaction/restart persistence proof and explicit tamper/archive limitations |

Use deterministic fake time and synchronization barriers for races; test restart using durable state, not process-memory rehydration disguised as durability. Hidden/nonexistent results must have equal public shape/status/header/cache semantics, no existence-dependent external calls or counts, and bounded timing comparisons; exact constant wall-clock response time is not promised. Measure and investigate systematic timing differences. Test deny-before-fetch with spies that fail on protected retrieval, then test the actual scoped repositories where authorized test storage exists.

Record per-checkpoint revision/configuration, commands/counts, direct behavior, contract changes, sanitized correlation traces and unresolved integration gaps in existing checkpoint proof locations. Secrets and disposable logs stay outside the repository. Missing real provider/email flows, external revocation semantics, authorized persistence writes, transaction support or assurance proof remains an explicit unmet criterion; no full P02 completion from validator mocks or no-effect harnesses alone. No connector/model/production coverage is inferred.

## Authentication contracts and negative verification

These proposed canonical paths require BFF service authentication and fixed same-origin web handlers. Auth inputs reject unknown fields; passwords/proofs are write-only, examples contain placeholders. Public signup/reset/resend use the same `202 {status: "checkEmail", requestId}` for duplicate/known/unknown keys. Failed login uses `401 {code: "SIGN_IN_FAILED", requestId}` with universal provider guidance. Account-independent global outage/429 responses must not disclose method availability. A public session DTO exposes safe display data, permitted tenants and expiry, never proofs/handle. No membership yields empty authorized scope, never automatic tenant creation.

| Internal contract | Typed input / result |
| --- | --- |
| `POST /internal/v1/auth/registrations` | `{fullName: string[1..120], email: EmailInput, password: PasswordInput, transactionId: UUID}` → generic acknowledgement |
| `POST /internal/v1/auth/email-verifications/confirm` | `{transactionId: UUID, token: SecretToken, password: PasswordInput}` + browser binding → completion, no session |
| `POST /internal/v1/auth/email-verifications/resend` | `{email: EmailInput, transactionId: UUID}` → generic acknowledgement |
| `POST /internal/v1/auth/password-sessions` | `{email: EmailInput, password: PasswordInput, transactionId: UUID}` → internal handle/expiry or fixed failure |
| `POST /internal/v1/auth/provider-exchanges` | Discriminated Google ID-token/GitHub access-token proof plus transaction; expected provider/client/nonce resolved server-side → internal handle or restricted challenge |
| `POST /internal/v1/auth/password-resets` and `/confirm` | Start `{email, transactionId}` → generic acknowledgement; confirm `{transactionId, token, newPassword}` + binding → no session |
| `POST /internal/v1/account/sign-in-methods/intents` and `/confirm` | Canonical session + recent existing-method proof, `{method, expectedAccountRevision}`, then bound target proof and explicit confirmation → atomic link and session rotation |
| `DELETE /internal/v1/account/sign-in-methods/{method}` | Session, recent independent retained-method proof, revision/idempotency → refuse last usable method removal |

Define a separate strict `verifyEmail` confirmation variant without password for non-authoritative Google email. It requires the still-valid bound provider transaction/proof and never activates a pending password. After independent provider validation, retain only a short-lived canonical verified-result record (subject, evidence kind, email, checked time, transaction/purpose and expiry), not the provider token; its expiry cannot exceed the original proof/transaction. The mailbox challenge cannot create a tenant session by itself. Missing social full name uses a restricted `{transactionId, fullName}` completion contract before account/session creation. Recheck uniqueness and evidence expiry at final creation.

Link confirmation is a strict discriminated union: `{method: "password", intentId, newPassword, mailboxToken, expectedAccountRevision}` or `{method: "google"|"github", intentId, providerExchangeId, expectedAccountRevision}`. Proof references are server-owned, one-use and bound to initiating session/account/purpose; browser-supplied IDs alone grant nothing. Reauthentication produces a short-lived server reference bound to that same intent and epoch, not an arbitrary client timestamp. Adding a password never stores it before all existing-method/mailbox checks pass. Transaction creation is BFF-authenticated, purpose-bound and rate-limited; no global lookup. Reset/signup cross-device links offer restart rather than dropping browser binding. Password/SecretToken types use the bounded rules above. Canonical auth responses remain private/no-store and never expose link-conflict details through public NextAuth error URLs.

| Negative group | Required proof before P02.2 acceptance |
| --- | --- |
| Provider truth | Google false/missing/malformed verification, third-party mailbox challenge, wrong client/nonce/issuer, expiry/key rotation/outage; GitHub null/private/changed email, missing scope, unverified primary, placeholder/noreply, multiple verified addresses, incomplete pagination, 401/403/429/timeout; no session on inadequate evidence |
| Pre-hijack/collision | Attacker pending signup then victim social login, victim clicks attacker proof, normalized-email signup/provider/link/verification races, subject bound elsewhere and changed provider email; no inherited password, duplicate account, implicit merge or privilege grant |
| Proof lifecycle | Wrong-purpose/account/generation/browser, expiry, GET scanner, concurrent consume/resend/reset, restart/replay and storage failure; one accepted state transition with durable audit, no auto-login |
| Credential abuse | Known/unknown/social-only/pending/suspended/bad-password and duplicate signup/reset/resend compare body/status/header/timing; distributed limits/dummy hashing, hash-budget exhaustion, oversized input and versioned rehash |
| Linking/recovery | Google user fails password safely then explicitly adds it after Google auth; password user links provider; ordinary signed-in `signIn`, stolen session alone, stale reauth, CSRF, wrong subject/email, last-method races and reset-to-add-password denied |
| Mail/degraded state | Real authorized verification/reset delivery and consumption (sandbox is not delivery proof), accepted versus bounced/timeout/duplicate/out-of-order, forged/replayed events, suppression/quota/resend invalidation; delivery never activates |
| Sessions/assurance | Cookie after logout/reset/deprovisioning, copied cookie/handle without BFF, client serialization, rolling-expiry bypass, provider revocation lag; supported step-up success/failure before P02.4 acceptance |

## Reference basis and decisions still needed

Research checked 11 November 2026. Provider/library facts are linked at the relevant boundaries; application policies remain proposals. [Auth.js documentation scope](https://authjs.dev/getting-started) distinguishes v5 from v4 guidance; [NextAuth linking FAQ](https://next-auth.js.org/faq) explains same-email trust risks. [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html) and [OAuth Security BCP](https://www.rfc-editor.org/rfc/rfc9700.html) inform code-flow validation. [MongoDB atomicity](https://www.mongodb.com/docs/manual/core/write-operations-atomicity/) and [transactions](https://www.mongodb.com/docs/manual/core/transactions/) support conditional writes; deployment capability remains unverified.

Before dependent implementation accept: exact NextAuth/Python verifier/Argon2 pins and compatibility; canonical JWT/session bridge and BFF/workload credential scheme; normalization/pending-account policy; password/lifetime/rate-limit values; provider evidence/freshness/external revocation lag; account-management reauthentication versus sensitive-action assurance; restricted recovery/unlink policy; SendGrid service/sender/region and authorized sending; role inheritance/production grants; authorized non-production persistence/migration/transaction proof. Record accepted choices before depending on them; this proposal does not amend decisions. No provisioning, product data writes or spending is approved, and read-only foundation credentials supply no write permission.
