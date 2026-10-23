# P13 — Release 1 integration and readiness

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P01–P12.
**Phase outcome:** acceptance journeys for the trustworthy loop pass across roles and failure states.

## Purpose and scope

Prove the complete Release 1 trust loop under realistic success and failure conditions.

**Included:** GitHub/Actions/Jira/Azure/Vercel journey demonstrations, accessibility, measurements, documentation, and release decision.
**Critical failure boundary:** An attractive happy-path demo alone does not satisfy the gate.

## Overall phase acceptance

- The phase outcome is demonstrated: Acceptance journeys for the trustworthy loop pass across roles and failure states.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P13.1 — Run end-to-end failed-run and alert-to-verified-PR scenarios on the reference demo service

**Status:** Not started.
**Expected result:** Run end-to-end failed-run and alert-to-verified-PR scenarios on the reference demo service.

**Acceptance criteria**

- Failed run and alert each reach reviewed evidence, justified proposal, verified draft PR, observed outcome and replay. Both GitHub → Actions → Jira → Azure and GitHub → Actions → Jira → Vercel lineage are demonstrated with exact revisions and provider receipts.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P13.2 — Review keyboard accessibility, role permissions, partial data, and stale provider states

**Status:** Not started.
**Expected result:** Review keyboard accessibility, role permissions, partial data, and stale provider states.

**Acceptance criteria**

- Role matrix, keyboard paths, stale/partial/denied states and connector outage pass documented reviews.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P13.3 — Measure setup time, time to decisive evidence, user comprehension, and AI evaluation gates

**Status:** Not started.
**Expected result:** Measure setup time, time to decisive evidence, user comprehension, and AI evaluation gates.

**Acceptance criteria**

- Setup and time-to-evidence measurements, comprehension tasks and AI evaluation metrics meet the thresholds accepted in P00.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P13.4 — Publish runbooks, Swagger docs, architecture decisions, threat model, and recovery demo

**Status:** Not started.
**Expected result:** Publish runbooks, Swagger docs, architecture decisions, threat model, and recovery demo.

**Acceptance criteria**

- Operator runbooks, current OpenAPI/Swagger, decisions, threat model and recovery procedure match the deployed candidate.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P13.5 — Record explicit release decision with gaps and evidence; archive a replay baseline

**Status:** Not started.
**Expected result:** Record explicit release decision with gaps and evidence; archive a replay baseline.

**Acceptance criteria**

- Release record lists pass/fail evidence, open gaps, owner and rollback plan; replay baseline is immutable and accessible.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
