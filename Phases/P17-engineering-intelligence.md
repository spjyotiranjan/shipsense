# P17 — Engineering intelligence

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P13–P16.
**Phase outcome:** metrics drill to source data with disclosed definitions and coverage.

## Purpose and scope

Show delivery and reliability trends with transparent definitions and source lineage.

**Included:** DORA, quality/automation, role views, cost, and data validation.
**Critical failure boundary:** Aggregated metrics must not rank individual developers or hide missing coverage.

## Overall phase acceptance

- The phase outcome is demonstrated: Metrics drill to source data with disclosed definitions and coverage.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P17.1 — Compute current DORA metrics and SLO/incident trends with definition/version controls

**Status:** Not started.
**Expected result:** Compute current DORA metrics and SLO/incident trends with definition/version controls.

**Acceptance criteria**

- Five current DORA metrics and SLO/incident calculations match golden data with declared definitions, windows and sources.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P17.2 — Add flaky test, rework, automation acceptance, abstention, and false-positive measures

**Status:** Not started.
**Expected result:** Add flaky test, rework, automation acceptance, abstention, and false-positive measures.

**Acceptance criteria**

- Flaky/rework/automation rates drill to underlying cases and disclose missing or changed inputs.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P17.3 — Add role-scoped dashboards and exports; avoid individual productivity scoring

**Status:** Not started.
**Expected result:** Add role-scoped dashboards and exports; avoid individual productivity scoring.

**Acceptance criteria**

- Role-scoped dashboards enforce authorization and avoid individual scoreboards; exports preserve definition and coverage metadata.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P17.4 — Add cost attribution for AI, storage, telemetry queries, and connectors

**Status:** Not started.
**Expected result:** Add cost attribution for AI, storage, telemetry queries, and connectors.

**Acceptance criteria**

- AI/storage/query/connector cost estimates reconcile with billed or sampled usage and expose uncertainty.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P17.5 — Review metrics against golden data and missing-source scenarios

**Status:** Not started.
**Expected result:** Review metrics against golden data and missing-source scenarios.

**Acceptance criteria**

- Golden and missing-source fixtures detect definition drift and prevent incompatible comparisons from appearing as clean trends.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
