# P02 — Identity, tenancy, permissions, and audit

**Current status:** In progress. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P01.
**Phase outcome:** denied access never exposes another tenant; all material decisions have correlated audit records.

## Purpose and scope

Enforce identity and authorization consistently across the web, API, workers, connectors, and AI tools.

**Included:** Tenant model, sessions, resource permissions, approvals, and audit.
**Critical failure boundary:** No denied tenant or protected object may be exposed through a side channel.

## Overall phase acceptance

- The phase outcome is demonstrated: Denied access never exposes another tenant; all material decisions have correlated audit records.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or GitHub/source evidence.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P02.1 — Define organizations, projects, teams, services, environments, users, roles, and service accounts

**Status:** In progress. Schema/role foundation is implemented in [`packages/domain`](../packages/domain/README.md), with canonical OpenAPI/TypeScript schemas and [targeted negatives](../packages/domain/tests/test_identity.py). No administration routes, persistent mutations or authenticated UI are delivered; the bounded foundation was accepted through [PR #10](https://github.com/spjyotiranjan/shipsense/pull/10), while full checkpoint exit proof remains pending. See the checkpoint record in `../PROJECT_STATUS.md`.
**Expected result:** Define organizations, projects, teams, services, environments, users, roles, and service accounts.

**Acceptance criteria**

- Entity schemas and role matrix define organization, project, service, environment, team, user, and service-account boundaries with ownership and lifecycle.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

### P02.2 — Implement login/session and token validation across web, API, workers, and provider callbacks

**Status:** In progress. The disabled-by-default [session bridge](../docs/session-bridge.md) implements cookie-only NextAuth handling, bounded expiry, BFF service credentials and canonical authority ports under [Decision 0010](../docs/decisions/0010-p02-session-bridge.md). [Web](../apps/web/tests/session-bridge.test.ts) and [API](../services/api/tests/test_session_bridge.py) tests cover synthetic authority, actual credential interoperability and failure boundaries. Real providers, persistent authority, worker/callback isolation and external revocation proof remain pending; this is not checkpoint completion.
**Expected result:** Implement login/session and token validation across web, API, workers, and provider callbacks.

**Acceptance criteria**

- Expired, forged, revoked, and wrong-audience credentials fail in web/API/worker callback paths; logout and deprovisioning take effect.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

### P02.3 — Enforce tenant/resource/environment permissions at every API and tool call; test negative cases

**Status:** Not started.
**Expected result:** Enforce tenant/resource/environment permissions at every API and tool call; test negative cases.

**Acceptance criteria**

- Negative tests deny cross-tenant and cross-environment reads and effects, including AI tool calls, counts, suggestions, and errors.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

### P02.4 — Add policy decisions, separation of duties, expiring approvals, and step-up for sensitive actions

**Status:** Not started.
**Expected result:** Add policy decisions, separation of duties, expiring approvals, and step-up for sensitive actions.

**Acceptance criteria**

- Approval binds to exact version, role, and expiry; proposer self-approval and material-change reuse are rejected with audit reasons.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

### P02.5 — Record immutable-at-application-level audit events; plan tamper evidence and export

**Status:** In progress. The [canonical session transaction contract](../docs/session-bridge.md#verification-and-remaining-gates) requires redacted correlated audit before releasing resolve/revoke success, with [synthetic rollback/race tests](../services/api/tests/test_canonical_sessions.py). No durable adapter, tenant reconstruction, database concurrency/restart proof or archive is claimed.
**Expected result:** Record immutable-at-application-level audit events; plan tamper evidence and export.

**Acceptance criteria**

- Sensitive reads, policy decisions, approvals, effects, and provider receipts share correlation IDs and can be reconstructed chronologically.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
