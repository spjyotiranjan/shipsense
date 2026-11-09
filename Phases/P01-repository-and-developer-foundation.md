# P01 â€” Repository and developer foundation

**Current status:** In progress (9 November 2026). P01.1/2 accepted with PR #4/#5 merged; SCRUM-15 bounded local core is accepted but unmerged; SCRUM-16 accepted but PR #8 unmerged; SCRUM-17 clean integration CI is in progress and phase exit remains unverified. See [current proof and limitations](../PROJECT_STATUS.md).
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

### P01.1 â€” Establish `apps/web`, `services/api`, `services/worker`, `packages/contracts`, `infra`, `docs`, and test fixtures

**Status:** Complete; accepted 9 November 2026.
**Proof:** [SCRUM-13 acceptance and verification](https://spjyotiranjan.atlassian.net/browse/SCRUM-13?focusedCommentId=10003), [merged PR #4](https://github.com/spjyotiranjan/shipsense/pull/4), accepted head `e4d1efbf6e97085738556f9b968471af8b348ddd`. Local builds/startup/browser/failure checks, independent exact-SHA review and acceptance recorded. Foundation had zero CI checks; full CI remains P01.5.

**Expected result:** Establish `apps/web`, `services/api`, `services/worker`, `packages/contracts`, `infra`, `docs`, and test fixtures.

**Acceptance criteria**

- All named folders exist with README ownership and a minimal buildable package or service boundary.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P01.2 â€” Pin language/tool versions, lockfiles, formatting, linting, typing, secret scanning, and branch checks

**Status:** Complete; accepted 9 November 2026.
**Proof:** [SCRUM-14 quality, seeded local/CI rejection and recovery evidence](https://spjyotiranjan.atlassian.net/browse/SCRUM-14), [merged PR #5](https://github.com/spjyotiranjan/shipsense/pull/5), accepted head `d70c3f1`. Frozen installs, valid ESLint 9.39.5 peer tree, format/lint/typing/offline-secret/byte-level contract checks, affected builds/startup, independent exact-SHA review and acceptance recorded. Development minimatch advisory, Starlette/httpx deprecation and Decision 0003 validator-lifecycle limits remain disclosed in PROJECT_STATUS.md; full integration CI remains P01.5.
**Expected result:** Pin language/tool versions, lockfiles, formatting, linting, typing, secret scanning, and branch checks.

**Acceptance criteria**

- Tool versions and lockfiles are committed; lint, format, type, and secret checks fail CI on a seeded violation.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P01.3 â€” Add local MongoDB, queue emulator/adapter, R2 compatible development storage, and seeded demo data

**Status:** Bounded local core accepted at `c441de1` on 9 November 2026; [acceptance/Done](https://spjyotiranjan.atlassian.net/browse/SCRUM-15?focusedCommentId=10011), [PR #7](https://github.com/spjyotiranjan/shipsense/pull/7) merge remains pending. Issuer/reference runtime validation and other phase exit gates are not complete.
**Implementation/proof:** [runbook](../infra/local/README.md), [shared local adapters](../packages/local-core/src/shipsense_local), [safety tests](../packages/local-core/tests/test_unit.py), [real Mongo/S3 integration and outage tests](../packages/local-core/tests/test_integration.py), [six inert scoped fixtures](../tests/fixtures/p01) and [SCRUM-15](https://spjyotiranjan.atlassian.net/browse/SCRUM-15). Decision 0007 controls digest/client pins and private-access/integrity requirements. The core excludes issuer/reference runtime, full API readiness wiring, production parity and paid provisioning; those remain phase exit gates.
**Expected result:** Add local MongoDB, queue emulator/adapter, R2 compatible development storage, and seeded demo data.

**Acceptance criteria**

- A new developer can start seeded local services from documented commands without cloud credentials.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P01.4 â€” Build Next.js shell and FastAPI health/version endpoints; document Swagger/OpenAPI contracts

**Status:** Complete; accepted 9 November 2026 at `94279641cf4660b4a991db7af8c69b5e54b1a889`, stacked base `c441de1`. [Acceptance/Done](https://spjyotiranjan.atlassian.net/browse/SCRUM-16?focusedCommentId=10015), [exact-revision independent clearance](https://github.com/spjyotiranjan/shipsense/pull/8#issuecomment-6744104125); PR #8 remains unmerged. Credential-free PR #6 remains merged.
**Implementation:** [canonical API](../services/api/src/shipsense_api/main.py), [bounded readiness interface](../services/api/src/shipsense_api/diagnostics.py), [contract/failure tests](../services/api/tests/test_diagnostics.py) and [generated OpenAPI](../packages/contracts/openapi.json). Default startup exposes version/liveness/schema without backing services and keeps readiness503. Explicit validated external local configuration enables [owned real Mongo/S3 and same-process queue](../services/api/src/shipsense_api/local_readiness.py). [Real integration tests](../services/api/tests/test_readiness_integration.py) and direct HTTP proof exercise configured200, separate Mongo/storage200-to-503-to-200 with live/version/web remaining200, bounded storage deadlines/capacity/cancellation, queue unavailable/recovery and clean restart/shutdown. [Configuration/lifecycle tests](../services/api/tests/test_local_lifespan.py) cover invalid/missing/foreign configuration and redaction. Public OpenAPI is unchanged. Local/direct proof, exact-current-revision independent clearance, required remote checks and acceptance passed; P01.4 completion is separate from PR #8 landing and full P01 exit.
**Implementation prerequisite:** tested accepted SCRUM-13/14 supports credential-free canonical version/liveness/safe-error contracts and subsequent web diagnostic integration without SCRUM-15.
**Full acceptance prerequisite:** SCRUM-15 local adapters, seeded dependencies and real readiness outage/recovery proof; no mocked readiness substitution. Preserve all criteria below and in both technical plans.
**Web implementation:** [diagnostic UI](../apps/web/src/components/foundation-status.tsx), [same-origin route](../apps/web/src/app/api/foundation/route.ts), [bounded transport](../apps/web/src/lib/server/api-transport.ts) and [failure/race tests](../apps/web/tests/diagnostics.test.ts). Run the [web reproduction and verification commands](../apps/web/README.md). Safe transport errors share the generated canonical envelope. Connected indicates API reachability only. Full readiness and phase exit remain unverified.
**Expected result:** Build Next.js shell and FastAPI health/version endpoints; document Swagger/OpenAPI contracts.

**Acceptance criteria**

- The web calls a versioned FastAPI endpoint; OpenAPI and Swagger show matching request/response shapes and an error example.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P01.5 â€” Create CI that builds both apps and runs contract, unit, and smoke checks

**Status:** In progress; [SCRUM-17](https://spjyotiranjan.atlassian.net/browse/SCRUM-17). Maintained [local/CI commands](../docs/developer-setup.md#clean-integration-commands), [workflow](../.github/workflows/integration.yml), [fresh real smoke](../scripts/integration-smoke.py) and [failure/recovery gates](../scripts/verify-integration-gates.py) are implemented. Primary local quality/contracts/units/builds and real positive-negative-recovery/cancellation proof passed; clean remote runtime evidence, independent review and acceptance remain delivery gates.
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

## Phase kickoff â€” 8 November 2026

- Jira: [SCRUM-23](https://spjyotiranjan.atlassian.net/browse/SCRUM-23), board 1, existing user-started active `SCRUM Sprint 1` (36), with SCRUM-13â€“SCRUM-17 linked to this epic. Sprint dates, team allocation and closure remain manual.
- Corrected technical web/backend plans approved on 8 November 2026; bounded dependency adjustment recorded 9 November 2026. P01.1/SCRUM-13 and P01.2/SCRUM-14 accepted and merged; subsequent subphases retain their full technical gates.
