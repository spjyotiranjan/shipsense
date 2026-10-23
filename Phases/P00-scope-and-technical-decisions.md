# P00 — Scope and technical decisions

**Current status:** Complete. This phase contains planning and Jira setup, not product implementation.
**Prerequisites:** product PDF and owner's stack choices.
**Phase outcome:** accepted decision records, an active P00 Jira backlog, and an agreed Release 1 reference scenario.

## Purpose and scope

Turn the product vision and selected stack into explicit, reviewable decisions and an executable backlog.

**Included:** Product scope, reference integration pack, architecture choices, cost boundary, and Jira planning.
**Critical failure boundary:** An unresolved release boundary or an unowned decision cannot be treated as agreed.

## Overall phase acceptance

- The phase outcome is demonstrated: Accepted decision records, active-phase Jira backlog, and an agreed Release 1 reference scenario.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P00.1 — Read the product specification, including trust rules, acceptance journeys, and release contradictions

**Status:** Complete.
**Expected result:** Read the product specification, including trust rules, acceptance journeys, and release contradictions.

**Acceptance criteria**

- The review identifies the signature journey, non-negotiable trust rules, all 17 feature blueprints, and the conflicting integration assignments with source locations.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P00.2 — Record the owner's Next.js, FastAPI, MongoDB, R2, LangChain/LangGraph, OpenAI API, Swagger, Jira, and Azure choices

**Status:** Complete.
**Expected result:** Record the owner's Next.js, FastAPI, MongoDB, R2, LangChain/LangGraph, OpenAI API, Swagger, Jira, and Azure choices.

**Acceptance criteria**

- The stack record exactly matches the owner’s choices and distinguishes those choices from proposed Azure services and unselected model or identity options.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P00.3 — Write this roadmap, status method, and repository handoff

**Status:** Complete.
**Expected result:** Write this roadmap, status method, and repository handoff.

**Acceptance criteria**

- The roadmap names all phases, dependencies, exit gates, status meanings, and a usable handoff in the repository.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P00.4 — Decide Release 1 integration order, demo service, identity model, provisional region, spending controls, and measurable exit thresholds

**Status:** Complete; P01 validates region and cost forecast before provisioning.
**Expected result:** Accept the GitHub, Actions, Jira, Azure, and Vercel Release 1 scope; reference app, OIDC boundary, provisional Central India region, 20–30 user operating target, pre-provision cost forecast rule, and measurable gates.

**Acceptance criteria**

- Decision 0001 records the owner's provider breadth, reference application, identity approach, provisional region, operating target, and measurable acceptance thresholds. No numeric ceiling is invented; P01 requires an itemized forecast and owner spending decision before paid provisioning.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P00.5 — Record architecture decisions for Azure services, MongoDB hosting, queue/worker model, R2 retention, provider credentials, and model selection

**Status:** Complete; deployment-specific values have later validation gates.
**Expected result:** Accept the architecture baseline and explicitly assign SKU, OIDC issuer, model, and retention-day choices to measured implementation gates.

**Acceptance criteria**

- Decision 0002 dates the accepted baseline and records choices, alternatives, rationale, consequences, security boundaries, and validation gates. The fixed owner-selected stack is not silently substituted.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P00.6 — Configure phase-based Jira epics and sprints; create only the started P00 phase records

**Status:** Complete; sprint remains unstarted for manual scheduling.
**Expected result:** Record the phase-based Jira workflow in The Mentalists, then create the P00 epic and P00 sprint. The sprint contains P00.1–P00.6 as tasks with acceptance evidence and dependencies. Team assignments, estimates, dates, and sprint start are added manually later.

**Acceptance criteria**

- The Mentalists (SCRUM) has P00 epic SCRUM-6 and unstarted sprint 35; SCRUM-7 through SCRUM-12 are members of the sprint and children of the epic, with descriptions, evidence locations, and prerequisite notes. ShipSense future-phase epics and sprints are absent until those phases start.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: ShipSense owner scope answers and Jira setup, 23 October 2026.
- Evidence links: `../docs/decisions/0001-release-1-scope.md`, `../docs/decisions/0002-architecture-baseline.md`, `../docs/JIRA_WORKFLOW.md`, and Jira SCRUM-6–SCRUM-12.
- Open risks and owner: Owner approves a monetary ceiling before paid provisioning; P01 validates region and cost; sprint scheduling and team allocation are manual.
- Decision: P00 planning acceptance met; verify repository/Jira status sync before closing the phase.
