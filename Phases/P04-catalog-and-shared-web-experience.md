# P04 — Catalog and shared web experience

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P03.
**Phase outcome:** a user can find a service, see its owner and connections, and understand partial coverage.

## Purpose and scope

Give operators a coherent service-centric view before adding AI.

**Included:** Discovery, fleet, Service 360, scope, search, states, and accessibility.
**Critical failure boundary:** Unknown, stale, and incomplete coverage must never look healthy.

## Overall phase acceptance

- The phase outcome is demonstrated: A user can find a service, see its owner and connections, and understand partial coverage.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P04.1 — Implement service discovery, ownership, repository/environment mapping, and ambiguity review

**Status:** Not started.
**Expected result:** Implement service discovery, ownership, repository/environment mapping, and ambiguity review.

**Acceptance criteria**

- Conflicting service mappings enter review; an override is attributed, reversible, and does not silently merge identities.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P04.2 — Build fleet, catalog, Service 360, shared scope bar, search, timeline, and evidence drawer

**Status:** Not started.
**Expected result:** Build fleet, catalog, Service 360, shared scope bar, search, timeline, and evidence drawer.

**Acceptance criteria**

- A user can travel fleet → service → run/deployment/incident while retaining environment/time scope and opening evidence.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P04.3 — Add loading, empty, stale, denied, disconnected, rate limited, and historical states

**Status:** Not started.
**Expected result:** Add loading, empty, stale, denied, disconnected, rate limited, and historical states.

**Acceptance criteria**

- UI stories demonstrate every named state with explanation and available next action; unknown is visually and textually distinct.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P04.4 — Add accessible keyboard journeys and alternate table views for graphs

**Status:** Not started.
**Expected result:** Add accessible keyboard journeys and alternate table views for graphs.

**Acceptance criteria**

- Core journeys work by keyboard and screen reader; graphs have an equivalent accessible table and zoom/reflow remain usable.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P04.5 — Preserve exact object/time/environment scope in deep links and exports

**Status:** Not started.
**Expected result:** Preserve exact object/time/environment scope in deep links and exports.

**Acceptance criteria**

- Reloadable deep links and exports reproduce the same authorized object revision and time range, or explain why access changed.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
