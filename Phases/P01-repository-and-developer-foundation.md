# P01 — Repository and developer foundation

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P00 architecture decisions.
**Phase outcome:** reproducible local boot, automated checks, and a working web-to-API request.

## Purpose and scope

Establish a reproducible development workspace and the first working web-to-API slice.

**Included:** Repository structure, local services, quality checks, API contracts, and CI.
**Critical failure boundary:** A green local run that cannot be reproduced in CI does not pass.

## Overall phase acceptance

- The phase outcome is demonstrated: Reproducible local boot, automated checks, and a working web-to-API request.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P01.1 — Establish `apps/web`, `services/api`, `services/worker`, `packages/contracts`, `infra`, `docs`, and test fixtures

**Status:** Not started.
**Expected result:** Establish `apps/web`, `services/api`, `services/worker`, `packages/contracts`, `infra`, `docs`, and test fixtures.

**Acceptance criteria**

- All named folders exist with README ownership and a minimal buildable package or service boundary.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P01.2 — Pin language/tool versions, lockfiles, formatting, linting, typing, secret scanning, and branch checks

**Status:** Not started.
**Expected result:** Pin language/tool versions, lockfiles, formatting, linting, typing, secret scanning, and branch checks.

**Acceptance criteria**

- Tool versions and lockfiles are committed; lint, format, type, and secret checks fail CI on a seeded violation.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P01.3 — Add local MongoDB, queue emulator/adapter, R2 compatible development storage, and seeded demo data

**Status:** Not started.
**Expected result:** Add local MongoDB, queue emulator/adapter, R2 compatible development storage, and seeded demo data.

**Acceptance criteria**

- A new developer can start seeded local services from documented commands without cloud credentials.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P01.4 — Build Next.js shell and FastAPI health/version endpoints; document Swagger/OpenAPI contracts

**Status:** Not started.
**Expected result:** Build Next.js shell and FastAPI health/version endpoints; document Swagger/OpenAPI contracts.

**Acceptance criteria**

- The web calls a versioned FastAPI endpoint; OpenAPI and Swagger show matching request/response shapes and an error example.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P01.5 — Create CI that builds both apps and runs contract, unit, and smoke checks

**Status:** Not started.
**Expected result:** Create CI that builds both apps and runs contract, unit, and smoke checks.

**Acceptance criteria**

- Clean checkout CI builds both apps and runs the same documented contract and smoke checks as local development.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
