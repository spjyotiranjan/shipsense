# P11 — Governed remediation and verification

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P02, P05, P10.
**Phase outcome:** approved minimal patch opens a verified draft PR; unsafe proposals stop before effects.

## Purpose and scope

Turn supported hypotheses into bounded, verified, human-governed PRs and measured outcomes.

**Included:** Proposal state, isolated patching, checks, approval, draft PR, and merge-to-health observation.
**Critical failure boundary:** No generated production write, self-approval, unrelated diff, or weakened test.

## Overall phase acceptance

- The phase outcome is demonstrated: Approved minimal patch opens a verified draft PR; unsafe proposals stop before effects.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P11.1 — Define action proposal states, exact scope, path/dependency budget, expiry, and rollback plan

**Status:** Not started.
**Expected result:** Define action proposal states, exact scope, path/dependency budget, expiry, and rollback plan.

**Acceptance criteria**

- Proposal identifies exact base commit, allowed paths, size, causal evidence, checks, policy, approver, expiry and rollback.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P11.2 — Isolate candidate changes and verification jobs from production credentials and tenant data

**Status:** Not started.
**Expected result:** Isolate candidate changes and verification jobs from production credentials and tenant data.

**Acceptance criteria**

- Verification runs in isolated ephemeral scope without production credentials; escape and exfiltration attempts are blocked.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P11.3 — Run formatting, lint, type, tests, security, secret, policy, and unrelated-diff checks

**Status:** Not started.
**Expected result:** Run formatting, lint, type, tests, security, secret, policy, and unrelated-diff checks.

**Acceptance criteria**

- A failing format/test/security/policy/path check blocks PR creation and leaves an inspectable failure record.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P11.4 — Show evidence chain, alternatives, exact diff, checks, approver, and provider authority

**Status:** Not started.
**Expected result:** Show evidence chain, alternatives, exact diff, checks, approver, and provider authority.

**Acceptance criteria**

- Reviewer sees exact diff, alternatives, blast radius, verifier result and provider authority; stale approval is invalidated.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P11.5 — Open draft GitHub PR after eligible review; human/provider permissions control merge

**Status:** Not started.
**Expected result:** Open draft GitHub PR after eligible review; human/provider permissions control merge.

**Acceptance criteria**

- Only an eligible review opens a draft PR; merge remains governed by GitHub permissions and is not automatic.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P11.6 — Observe merge through CI, rollout, SLO, and incident recovery; classify healthy/regressed/inconclusive

**Status:** Not started.
**Expected result:** Observe merge through CI, rollout, SLO, and incident recovery; classify healthy/regressed/inconclusive.

**Acceptance criteria**

- Outcome distinguishes healthy, regressed, unrelated recovery and inconclusive by observing CI, rollout and service signals.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
