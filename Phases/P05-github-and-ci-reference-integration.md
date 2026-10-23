# P05 — GitHub, Actions, and Jira reference integration

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P03–P04.
**Phase outcome:** failed PR run is traceable to exact attempt, job, log, artifact, Jira work item, and affected service.

## Purpose and scope

Trace a GitHub change through exact CI attempts, Jira work items, and controlled manual actions.

**Included:** GitHub App, Actions events, DAG, tests/logs, Jira issue links and governed updates, provider controls, and failure fixture.
**Critical failure boundary:** Reruns must create a new attempt and preserve the first failure.

## Overall phase acceptance

- The phase outcome is demonstrated: Failed PR run is traceable to exact attempt, job, log, artifact, Jira work item, and affected service.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P05.1 — Connect GitHub App with least privilege, webhook verification, installation mapping, and revocation

**Status:** Not started.
**Expected result:** Connect GitHub App with least privilege, webhook verification, installation mapping, and revocation.

**Acceptance criteria**

- Installation preview shows scopes; signed webhook validation, token rotation/revocation, and wrong-installation denial pass tests.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P05.2 — Normalize commits, PRs, checks, Actions workflow runs, jobs, attempts, tests, and artifacts

**Status:** Not started.
**Expected result:** Normalize commits, PRs, checks, Actions workflow runs, jobs, attempts, tests, and artifacts.

**Acceptance criteria**

- Fixtures normalize PR/commit/check/run/job/attempt/test/artifact links without collapsing skipped, canceled, superseded, or timed-out states.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P05.3 — Render pipeline DAG, logs, test failure clusters, retry history, and superseded commits

**Status:** Not started.
**Expected result:** Render pipeline DAG, logs, test failure clusters, retry history, and superseded commits.

**Acceptance criteria**

- Failed job and comparison run are navigable; logs redact secrets and DAG has an accessible list alternative.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P05.4 — Offer authorized manual retry/cancel controls with provider receipt, idempotency, and policy

**Status:** Not started.
**Expected result:** Offer authorized manual retry/cancel controls with provider receipt, idempotency, and policy.

**Acceptance criteria**

- Authorized retry/cancel records policy, provider receipt and result; stale run or duplicate request cannot produce unintended extra effects.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P05.5 — Prove source-to-run-to-artifact lineage with a deliberate failing fixture

**Status:** Not started.
**Expected result:** Prove source-to-run-to-artifact lineage with a deliberate failing fixture.

**Acceptance criteria**

- A seeded failing PR can be traced to the exact affected service and artifact with source links and a reviewed next action.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P05.6 — Connect Jira work items to the delivery trail

**Status:** Not started.
**Expected result:** Connect customer Jira project and issue identity to service, PR, Actions run, deployment, incident, and corrective action. Support governed issue updates.

**Acceptance criteria**

- Installation maps allowed projects, issue types and fields with explicit provider permissions; signed webhook or polling backfill preserves revisions, missing fields and raw issue links.
- A fixture links an issue to an exact PR/check/run and affected service without guessing from a similar title; ambiguous links remain reviewable.
- Issue updates require current provider authority, ShipSense policy, actor, exact field diff, idempotency key, provider receipt and audit record. Revoked access fails closed.
- One denied-scope, stale-webhook, and duplicate-update path is demonstrated.

**Proof to attach:** Jira installation scope, mapping fixture, end-to-end trace, action receipt, and negative tests in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
