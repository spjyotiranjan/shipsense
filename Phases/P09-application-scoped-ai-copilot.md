# P09 — Application-scoped AI copilot

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P02–P08.
**Phase outcome:** cited explain/compare answers preserve scope and abstain on denied or stale decisive sources.

## Purpose and scope

Answer application questions with exact scope, visible source planning, and defensible claims.

**Included:** Context capsule, authorization, LangGraph state, OpenAI adapter, evidence UI, and adversarial tests.
**Critical failure boundary:** A fluent answer cannot hide source gaps or gain permission.

## Overall phase acceptance

- The phase outcome is demonstrated: Cited explain/compare answers preserve scope and abstain on denied or stale decisive sources.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P09.1 — Implement visible context capsule for tenant, service, environment, time, role, and source coverage

**Status:** Not started.
**Expected result:** Implement visible context capsule for tenant, service, environment, time, role, and source coverage.

**Acceptance criteria**

- Each turn shows tenant, service, environment, time, role, incident/release and source coverage; scope changes create a new revision.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P09.2 — Build authorized source planner with cost/time/data budgets and cancellation

**Status:** Not started.
**Expected result:** Build authorized source planner with cost/time/data budgets and cancellation.

**Acceptance criteria**

- Source plan explains order, cost and freshness; forbidden sources are excluded before retrieval; cancellation and budget exhaustion stop safely.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P09.3 — Use LangGraph for resumable turns and LangChain adapters where useful; persist scoped checkpoints in MongoDB

**Status:** Not started.
**Expected result:** Use LangGraph for resumable turns and LangChain adapters where useful; persist scoped checkpoints in MongoDB.

**Acceptance criteria**

- A saved turn resumes after interruption without cross-user memory; checkpoints honor tenant, user, service, and retention boundaries.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P09.4 — Use OpenAI API behind a model adapter; require structured claim/evidence outputs and log version/cost

**Status:** Not started.
**Expected result:** Use OpenAI API behind a model adapter; require structured claim/evidence outputs and log version/cost.

**Acceptance criteria**

- Structured output validates claims/citations and captures model, prompt, tool, tokens, latency, and cost without exposing secrets.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P09.5 — Display facts, interpretations, contradictions, gaps, confidence limits, source links, and correction history

**Status:** Not started.
**Expected result:** Display facts, interpretations, contradictions, gaps, confidence limits, source links, and correction history.

**Acceptance criteria**

- Each material claim links to versioned evidence and contradictions; user correction preserves original claim and audit history.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P09.6 — Test cross-tenant leaks, injected logs/runbooks, revoked access, stale memory, and tool failures

**Status:** Not started.
**Expected result:** Test cross-tenant leaks, injected logs/runbooks, revoked access, stale memory, and tool failures.

**Acceptance criteria**

- Adversarial fixtures prove zero protected-content leakage and no action from injected log/runbook instructions; stale decisive evidence yields abstention.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
