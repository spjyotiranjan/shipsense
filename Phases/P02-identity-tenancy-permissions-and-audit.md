# P02 — Identity, tenancy, permissions, and audit

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P01.
**Phase outcome:** denied access never exposes another tenant; all material decisions have correlated audit records.

## Purpose and scope

Enforce identity and authorization consistently across the web, API, workers, connectors, and AI tools.

**Included:** Tenant model, sessions, resource permissions, approvals, and audit.
**Critical failure boundary:** No denied tenant or protected object may be exposed through a side channel.

## Overall phase acceptance

- The phase outcome is demonstrated: Denied access never exposes another tenant; all material decisions have correlated audit records.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P02.1 — Define organizations, projects, teams, services, environments, users, roles, and service accounts

**Status:** Not started.
**Expected result:** Define organizations, projects, teams, services, environments, users, roles, and service accounts.

**Acceptance criteria**

- Entity schemas and role matrix define organization, project, service, environment, team, user, and service-account boundaries with ownership and lifecycle.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P02.2 — Implement login/session and token validation across web, API, workers, and provider callbacks

**Status:** Not started.
**Expected result:** Implement login/session and token validation across web, API, workers, and provider callbacks.

**Acceptance criteria**

- Expired, forged, revoked, and wrong-audience credentials fail in web/API/worker callback paths; logout and deprovisioning take effect.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P02.3 — Enforce tenant/resource/environment permissions at every API and tool call; test negative cases

**Status:** Not started.
**Expected result:** Enforce tenant/resource/environment permissions at every API and tool call; test negative cases.

**Acceptance criteria**

- Negative tests deny cross-tenant and cross-environment reads and effects, including AI tool calls, counts, suggestions, and errors.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P02.4 — Add policy decisions, separation of duties, expiring approvals, and step-up for sensitive actions

**Status:** Not started.
**Expected result:** Add policy decisions, separation of duties, expiring approvals, and step-up for sensitive actions.

**Acceptance criteria**

- Approval binds to exact version, role, and expiry; proposer self-approval and material-change reuse are rejected with audit reasons.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P02.5 — Record immutable-at-application-level audit events; plan tamper evidence and export

**Status:** Not started.
**Expected result:** Record immutable-at-application-level audit events; plan tamper evidence and export.

**Acceptance criteria**

- Sensitive reads, policy decisions, approvals, effects, and provider receipts share correlation IDs and can be reconstructed chronologically.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
