# P03 — Data, events, and evidence foundation

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P02.
**Phase outcome:** duplicate or reordered events yield the same current state and preserved history.

## Purpose and scope

Create a reliable, time-aware evidence backbone across providers.

**Included:** Canonical identities, MongoDB models, ingest, R2 snapshots, and provenance.
**Critical failure boundary:** Retries and source disorder must preserve history and converge on the correct current view.

## Overall phase acceptance

- The phase outcome is demonstrated: Duplicate or reordered events yield the same current state and preserved history.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P03.1 — Define canonical IDs and state machines for service, run, artifact, release, incident, investigation, proposal, and outcome

**Status:** Not started.
**Expected result:** Define canonical IDs and state machines for service, run, artifact, release, incident, investigation, proposal, and outcome.

**Acceptance criteria**

- Documented state machines reject invalid transitions and preserve previous attempts and superseded versions.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P03.2 — Design MongoDB collections, indexes, retention, tenant boundaries, and schema migration rules

**Status:** Not started.
**Expected result:** Design MongoDB collections, indexes, retention, tenant boundaries, and schema migration rules.

**Acceptance criteria**

- Indexes support tenant-scoped queries; migrations and retention rules are reversible/tested on seeded data.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P03.3 — Implement signed webhook ingestion, polling/backfill, idempotency, retries, dead letters, and reconciliation

**Status:** Not started.
**Expected result:** Implement signed webhook ingestion, polling/backfill, idempotency, retries, dead letters, and reconciliation.

**Acceptance criteria**

- Duplicate and reordered webhook fixtures produce one logical outcome; failed processing reaches retry/dead-letter and reconciliation paths.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P03.4 — Store evidence metadata in MongoDB and bounded binary snapshots in private R2 with checksums and expiry

**Status:** Not started.
**Expected result:** Store evidence metadata in MongoDB and bounded binary snapshots in private R2 with checksums and expiry.

**Acceptance criteria**

- R2 access is private and scoped; metadata, checksums, expiry, redaction, and deletion are verified without storing secret values.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P03.5 — Build provenance and freshness fields: provider object, version, valid/observed time, access result, and source link

**Status:** Not started.
**Expected result:** Build provenance and freshness fields: provider object, version, valid/observed time, access result, and source link.

**Acceptance criteria**

- Every displayed material claim opens provider object/version, observed and valid time, access result, freshness, and historical context.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
