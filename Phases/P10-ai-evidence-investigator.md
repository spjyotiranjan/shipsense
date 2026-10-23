# P10 — AI evidence investigator

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P09.
**Phase outcome:** a failed run or incident yields a reviewable multi-hypothesis report or explicit abstention.

## Purpose and scope

Produce reviewable investigations instead of opaque root-cause statements.

**Included:** Time-frozen collection, multiple hypotheses, disconfirmation, calibrated uncertainty, and reviewer feedback.
**Critical failure boundary:** Insufficient coverage must end in an explicit abstention.

## Overall phase acceptance

- The phase outcome is demonstrated: A failed run or incident yields a reviewable multi-hypothesis report or explicit abstention.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P10.1 — Freeze investigation scope, source versions, topology, and budget

**Status:** Not started.
**Expected result:** Freeze investigation scope, source versions, topology, and budget.

**Acceptance criteria**

- The report fixes tenant, incident, services, environment, time, source permissions and budget before collection.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P10.2 — Collect authorized code, CI, release, runtime, telemetry, alert, and knowledge evidence

**Status:** Not started.
**Expected result:** Collect authorized code, CI, release, runtime, telemetry, alert, and knowledge evidence.

**Acceptance criteria**

- A bounded evidence manifest covers available planes with source/version/time and records denied or missing data.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P10.3 — Rank multiple plausible hypotheses with support, disconfirmation, contradiction, and missing evidence

**Status:** Not started.
**Expected result:** Rank multiple plausible hypotheses with support, disconfirmation, contradiction, and missing evidence.

**Acceptance criteria**

- At least two plausible hypotheses appear when supported, each with support, contradiction, missing evidence and a test that could disprove it.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P10.4 — Cap confidence by coverage and source quality; stop on insufficient evidence

**Status:** Not started.
**Expected result:** Cap confidence by coverage and source quality; stop on insufficient evidence.

**Acceptance criteria**

- Confidence cannot exceed coverage limits; stale/contradictory sources or budget failure produce a reasoned stop with next evidence step.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P10.5 — Let users challenge claims and persist report/evidence manifest for audit and replay

**Status:** Not started.
**Expected result:** Let users challenge claims and persist report/evidence manifest for audit and replay.

**Acceptance criteria**

- Reviewer corrections and rejected hypotheses persist with before/after history and can become replay cases.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
