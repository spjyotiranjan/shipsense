# P12 — Replay and evaluation lab

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P09–P11.
**Phase outcome:** fixed cases reproduce outcomes and an unsafe regression blocks a release.

## Purpose and scope

Make AI and policy changes measurable through frozen cases and release gates.

**Included:** Fixture sanitation, labels, replay, scorecards, and unsafe regression handling.
**Critical failure boundary:** An unsafe individual case cannot be averaged away.

## Overall phase acceptance

- The phase outcome is demonstrated: Fixed cases reproduce outcomes and an unsafe regression blocks a release.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P12.1 — Convert synthetic or consented incidents into sanitized, tenant-isolated fixtures in R2

**Status:** Not started.
**Expected result:** Convert synthetic or consented incidents into sanitized, tenant-isolated fixtures in R2.

**Acceptance criteria**

- Fixture has consent/classification, tenant isolation, redacted identities/secrets, stable inputs and expiry.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P12.2 — Freeze expected evidence, causes, prohibited actions, abstention, and version metadata

**Status:** Not started.
**Expected result:** Freeze expected evidence, causes, prohibited actions, abstention, and version metadata.

**Acceptance criteria**

- Expected evidence, causes, unsafe actions and abstention labels are frozen and hidden from the tested run.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P12.3 — Replay model/prompt/tool/policy versions under identical inputs with hidden labels

**Status:** Not started.
**Expected result:** Replay model/prompt/tool/policy versions under identical inputs with hidden labels.

**Acceptance criteria**

- Runs record identical case inputs plus model/prompt/tool/policy versions; repeat runs are comparable or nondeterminism is declared.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P12.4 — Report citation precision/coverage, contradiction, cause rank, abstention, safety, cost, and latency

**Status:** Not started.
**Expected result:** Report citation precision/coverage, contradiction, cause rank, abstention, safety, cost, and latency.

**Acceptance criteria**

- Dashboard shows per-case and aggregate evidence, citation, contradiction, cause, abstention, safety, latency and cost metrics.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P12.5 — Gate releases on zero authorization leakage/policy bypass/unsafe actions and specified quality thresholds

**Status:** Not started.
**Expected result:** Gate releases on zero authorization leakage/policy bypass/unsafe actions and specified quality thresholds.

**Acceptance criteria**

- Any authorization leakage, policy bypass or unsafe action blocks release; quality thresholds and override rationale are visible.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
