# P14 — Jenkins and Kubernetes/Argo delivery breadth

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P13 and connector contract.
**Phase outcome:** Jenkins runs and Kubernetes/Argo delivery state have full source links and authorized actions.

## Purpose and scope

Extend the Release 1 Jira connector and canonical delivery model to Jenkins and Kubernetes/Argo without weakening authorization.

**Included:** Advanced Jira release/field mappings, Jenkins builds, Kubernetes workload state, Argo CD/Rollouts history, manual actions, and provider failure behavior.
**Critical failure boundary:** Cross-tool correlation cannot silently merge unrelated projects, clusters, or runs.

## Overall phase acceptance

- The phase outcome is demonstrated: Jenkins runs and Kubernetes/Argo delivery state have full source links and authorized actions; Jira advanced mappings preserve Release 1 behavior.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P14.1 — Extend Release 1 Jira with release identity and complex field mappings

**Status:** Not started.
**Expected result:** Extend P05 Jira integration with release/version identity, complex field mappings and larger backfills.

**Acceptance criteria**

- Jira release/version identity and complex customer fields map without breaking P05 issue/PR/run links; larger backfills preserve revisions, unmapped fields, permissions and replayability.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P14.2 — Connect Kubernetes workload state and Argo CD/Rollouts history

**Status:** Not started.
**Expected result:** Connect read-first Kubernetes workload/controller state and Argo CD/Rollouts desired versus observed state, drift, and progressive rollout history.

**Acceptance criteria**

- Controller desired/current/available state, probes, events, rollout steps, drift, manual changes and source revisions remain distinct and historically inspectable. Controlled effects reuse the Release 1 policy/receipt framework.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P14.3 — Connect Jenkins jobs/builds/stages/tests/artifacts and map retries and parameters into canonical CI states

**Status:** Not started.
**Expected result:** Connect Jenkins jobs/builds/stages/tests/artifacts and map retries and parameters into canonical CI states.

**Acceptance criteria**

- Jenkins jobs, builds, stages, parameters, tests and artifacts map into canonical attempts while retaining raw provider links.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P14.4 — Add manual trigger/cancel/retry and AI proposal handoff through the same action framework

**Status:** Not started.
**Expected result:** Add manual trigger/cancel/retry and AI proposal handoff through the same action framework.

**Acceptance criteria**

- Retry/cancel/trigger and AI handoff pass the same action policy used for GitHub Actions; denied and duplicate attempts stop.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P14.5 — Validate denied scopes, rate limits, failure recovery, and parity with GitHub Actions flows

**Status:** Not started.
**Expected result:** Validate denied scopes, rate limits, failure recovery, and parity with GitHub Actions flows.

**Acceptance criteria**

- Fixtures cover revoked scope, rate limiting, malformed events, Jenkins outage and outcome parity with GitHub Actions.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
