# P07 — Connectors and control-plane continuity

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P05–P06.
**Phase outcome:** a disconnected provider makes affected surfaces stale/read-only without stopping customer delivery.

## Purpose and scope

Make integration health and control-plane degradation an explicit operator experience.

**Included:** Connector lifecycle, reconciliation, provider authority, rate limits, and outage drill.
**Critical failure boundary:** Customer CI/CD continues while ShipSense is impaired.

## Overall phase acceptance

- The phase outcome is demonstrated: A disconnected provider makes affected surfaces stale/read-only without stopping customer delivery.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P07.1 — Add connector install preview, scope review, mapping queue, health, lag, and revoke impact

**Status:** Not started.
**Expected result:** Add connector install preview, scope review, mapping queue, health, lag, and revoke impact.

**Acceptance criteria**

- Install preview, mapping conflicts, granted scopes, lag, last success, revoke impact, and owner are visible for each connector.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P07.2 — Add webhook/polling reconciliation for missed, duplicate, and out-of-order events

**Status:** Not started.
**Expected result:** Add webhook/polling reconciliation for missed, duplicate, and out-of-order events.

**Acceptance criteria**

- Missed, duplicate, and out-of-order events reconcile to a stable projection with preserved source history.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P07.3 — Show provider permissions separately from ShipSense permissions at action points

**Status:** Not started.
**Expected result:** Show provider permissions separately from ShipSense permissions at action points.

**Acceptance criteria**

- Every action states both ShipSense eligibility and provider authority, and denial explains the missing condition.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P07.4 — Build connector failure, rate-limit, reconnect, and backfill operator paths

**Status:** Not started.
**Expected result:** Build connector failure, rate-limit, reconnect, and backfill operator paths.

**Acceptance criteria**

- Disconnection or rate limit disables unsafe current controls, preserves allowed history, and offers a safe reconnect/backfill path.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P07.5 — Run an outage drill proving external CI/CD continues and history is reconciled

**Status:** Not started.
**Expected result:** Run an outage drill proving external CI/CD continues and history is reconciled.

**Acceptance criteria**

- Outage drill proves external delivery continues and recovered ShipSense catches up before showing current healthy state.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
