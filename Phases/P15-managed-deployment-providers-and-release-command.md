# P15 — Remaining managed deployment providers and release command

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P03, P06, P11, P13.
**Phase outcome:** each supported provider exposes honest capability labels, safe manual controls, and verified outcomes.

## Purpose and scope

Extend the Release 1 Azure/Vercel deployment contract to remaining managed providers and verify customer health.

**Included:** Netlify, Railway, and Render adapter capabilities; deployment identity, manual controls, release decisions, and post-deploy verification.
**Critical failure boundary:** Never invent a provider capability or treat provider success as customer recovery.

## Overall phase acceptance

- The phase outcome is demonstrated: Each supported provider exposes honest capability labels, safe manual controls, and verified outcomes.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P15.1 — Extend deployment adapter contract to Netlify, Railway, and Render

**Status:** Not started.
**Expected result:** Extend the P06 Azure/Vercel deployment contract to Netlify, Railway, and Render with a per-provider capability matrix.

**Acceptance criteria**

- Azure and Vercel Release 1 behavior remains covered; Netlify, Railway and Render each have tested support/unsupported capability entries and provider-version notes.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P15.2 — Map deployment, environment, artifact/revision, config metadata, logs, and provider receipts

**Status:** Not started.
**Expected result:** Map deployment, environment, artifact/revision, config metadata, logs, and provider receipts.

**Acceptance criteria**

- Every deployment links exact revision/artifact, environment, config metadata, actor, time and provider receipt; secret values remain hidden.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P15.3 — Add authorized trigger/promote/hold/rollback controls only where provider semantics support them

**Status:** Not started.
**Expected result:** Add authorized trigger/promote/hold/rollback controls only where provider semantics support them.

**Acceptance criteria**

- Only supported effects appear; each action rechecks provider authority, ShipSense policy, current state and approval.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P15.4 — Build release candidate, immutable artifact identity, policy checks, approvals, environment parity, and change window views

**Status:** Not started.
**Expected result:** Build release candidate, immutable artifact identity, policy checks, approvals, environment parity, and change window views.

**Acceptance criteria**

- Release candidate and approval bind to immutable artifact/config/policy version; drift or material change invalidates approval.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P15.5 — Verify actual post-deploy health and distinguish deploy success from customer recovery

**Status:** Not started.
**Expected result:** Verify actual post-deploy health and distinguish deploy success from customer recovery.

**Acceptance criteria**

- Health checks and telemetry compare baseline with outcome; inconclusive or unrelated recovery is shown separately from success.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
