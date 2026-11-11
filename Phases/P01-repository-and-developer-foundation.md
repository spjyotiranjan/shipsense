# P01 — Repository and developer foundation

**Scope update — 11 November 2026:** [Decision 0007 integration-test acceptance](../docs/decisions/0007-local-foundation-dependencies.md#integration-tests-without-a-hosted-verification-gate--11-november-2026) removes the separate hosted-verification and environment approval gates. Retain hosted MongoDB/private R2 application settings, validated `{base}-{profile}` naming and placeholder-only [.env.example](../.env.example). Existing integration tests may use private hosted settings; unsupported coverage stays explicit. [Integration CI](../.github/workflows/integration.yml) runs credential-free checks with the [documented commands](../docs/developer-setup.md#clean-integration-commands). No Docker/self-hosted fixtures or new infrastructure are required. Historical proof remains revision-specific; all other checkpoint and phase criteria remain.

**Current status:** In progress (9 November 2026). P01.1/2 accepted with PR #4/#5 merged; P01.3 bounded local core is accepted but unmerged; P01.4 accepted but PR #8 unmerged; P01.5 clean integration CI is in progress and phase exit remains unverified. See [current proof and limitations](../PROJECT_STATUS.md).
**Prerequisites:** P00 architecture decisions.
**Phase outcome:** reproducible local boot, automated checks, and a working web-to-API request.

## Purpose and scope

Establish a reproducible development workspace and the first working web-to-API slice.

**Included:** Repository structure, hosted client configuration, quality checks, API contracts, and CI.
**Critical failure boundary:** A green local run that cannot be reproduced in CI does not pass.

## Overall phase acceptance

- The phase outcome is demonstrated: Reproducible local boot, automated checks, and a working web-to-API request.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or GitHub/source evidence.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P01.1 — Establish `apps/web`, `services/api`, `services/worker`, `packages/contracts`, `infra`, `docs`, and test fixtures

**Status:** Complete; accepted 9 November 2026.
**Proof:** [P01.1 acceptance and verification](https://github.com/spjyotiranjan/shipsense/pull/4), [merged PR #4](https://github.com/spjyotiranjan/shipsense/pull/4), accepted head `e4d1efbf6e97085738556f9b968471af8b348ddd`. Local builds/startup/browser/failure checks, independent exact-SHA review and acceptance recorded. Foundation had zero CI checks; full CI remains P01.5.

**Expected result:** Establish `apps/web`, `services/api`, `services/worker`, `packages/contracts`, `infra`, `docs`, and test fixtures.

**Acceptance criteria**

- All named folders exist with README ownership and a minimal buildable package or service boundary.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

### P01.2 — Pin language/tool versions, lockfiles, formatting, linting, typing, secret scanning, and branch checks

**Status:** Complete; accepted 9 November 2026.
**Proof:** [P01.2 quality, seeded local/CI rejection and recovery evidence](https://github.com/spjyotiranjan/shipsense/pull/5), [merged PR #5](https://github.com/spjyotiranjan/shipsense/pull/5), accepted head `d70c3f1`. Frozen installs, valid ESLint 9.39.5 peer tree, format/lint/typing/offline-secret/byte-level contract checks, affected builds/startup, independent exact-SHA review and acceptance recorded. Development minimatch advisory, Starlette/httpx deprecation  remain disclosed in PROJECT_STATUS.md; full integration CI remains P01.5.
**Expected result:** Pin language/tool versions, lockfiles, formatting, linting, typing, secret scanning, and branch checks.

**Acceptance criteria**

- Tool versions and lockfiles are committed; lint, format, type, and secret checks fail CI on a seeded violation.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

### P01.3 — Configure hosted MongoDB/private R2 and a bounded no-effect queue

**Status:** In progress for the current hosted configuration/test revision. Author local hosted read/private-authentication checks and API/web/browser recovery passed on 11 November ([PR #9](https://github.com/spjyotiranjan/shipsense/pull/9)); Grace cleared `a9c4cd6` ([verdict](https://github.com/spjyotiranjan/shipsense/pull/9#issuecomment-6783173462)). Revised acceptance wording/workflow requires new revision review and acceptance; a separate hosted result/approval is no longer a gate. Historical synthetic core acceptance at `c441de1` ([PR #7](https://github.com/spjyotiranjan/shipsense/pull/7)) remains historical and unmerged; its self-hosted path is retired.

**Implementation:** [Hosted settings/clients](../services/api/src/shipsense_api/hosted.py), [API configuration](../services/api/README.md), [bounded shared storage](../packages/local-core/src/shipsense_local/adapters.py), [same-process queue](../packages/local-core/src/shipsense_local/queue.py), [SDK/config/lifecycle tests](../services/api/tests/test_hosted.py) and [shared utility tests](../packages/local-core/tests/test_unit.py).

**Acceptance criteria**

- A new developer supplies existing hosted settings privately using the placeholder-only example and documented command; no database/storage installation, container or seed is required.
- Strict server-only configuration, verified TLS and bounded clients enforce database/bucket scope. Missing/invalid values keep readiness 503 without preventing independent live/version/web diagnostics; public errors/logs hide secrets and endpoints.
- Retain integration tests. Existing real-connection support may use privately supplied non-production MongoDB/R2 settings for bounded scoped reads and authentication checks. Disclose unavailable or unsupported coverage; mocked SDK success and historical emulator proof do not establish live compatibility. No separate hosted-verification run/result/approval is required. No schema/seed/object writes, provisioning or provider disruption are permitted.
- Queue tests preserve duplicate/reorder/poison/expiry/timeout/capacity/no-effect behavior. Client tests cover deadlines, cancellation, denial/recovery, partial construction and draining shutdown.

**Proof to attach:** Current revision, configuration/test coverage, required check results and limitations. Preserve actual historical hosted results by revision without claiming unperformed remote results or skipped tests as passes.

### P01.4 — Build Next.js shell and FastAPI health/version endpoints; document Swagger/OpenAPI contracts

**Status:** Complete; accepted 9 November 2026 at `94279641cf4660b4a991db7af8c69b5e54b1a889`, stacked base `c441de1`. [Source PR](https://github.com/spjyotiranjan/shipsense/pull/8), [exact-revision independent clearance](https://github.com/spjyotiranjan/shipsense/pull/8#issuecomment-6744104125); PR #8 remains unmerged. Credential-free PR #6 remains merged.
**Implementation:** [canonical API](../services/api/src/shipsense_api/main.py), [bounded readiness interface](../services/api/src/shipsense_api/diagnostics.py), [contract/failure tests](../services/api/tests/test_diagnostics.py) and [generated OpenAPI](../packages/contracts/openapi.json). Default startup exposes version/liveness/schema without backing services and keeps readiness503. Historical external local configuration enabled [owned real Mongo/S3 and same-process queue](../services/api/src/shipsense_api/readiness_runtime.py). [Real integration tests](https://github.com/spjyotiranjan/shipsense/blob/94279641cf4660b4a991db7af8c69b5e54b1a889/services/api/tests/test_readiness_integration.py) and direct HTTP proof exercise configured200, separate Mongo/storage200-to-503-to-200 with live/version/web remaining200, bounded storage deadlines/capacity/cancellation, queue unavailable/recovery and clean restart/shutdown. [Configuration/lifecycle tests](../services/api/tests/test_hosted_lifespan.py) cover invalid/missing/foreign configuration and redaction. Public OpenAPI is unchanged. Local/direct proof, exact-current-revision independent clearance, required remote checks and acceptance passed; P01.4 completion is separate from PR #8 landing and full P01 exit.
**Implementation prerequisite:** tested accepted P01.1/P01.2 supports credential-free canonical version/liveness/safe-error contracts and subsequent web diagnostic integration without P01.3.
**Current hosted acceptance prerequisite:** P01.3 hosted configuration and integration-test criteria, safe configuration failure and local-owned API stop/retry/recovery. Separate local/protected remote hosted-verification results are not required. Preserve historical revision-bound acceptance without new containers or remote-service outages.
**Web implementation:** [diagnostic UI](../apps/web/src/components/foundation-status.tsx), [same-origin route](../apps/web/src/app/api/foundation/route.ts), [bounded transport](../apps/web/src/lib/server/api-transport.ts) and [failure/race tests](../apps/web/tests/diagnostics.test.ts). Run the [web reproduction and verification commands](../apps/web/README.md). Safe transport errors share the generated canonical envelope. Connected indicates API reachability only. Full readiness and phase exit remain unverified.
**Expected result:** Build Next.js shell and FastAPI health/version endpoints; document Swagger/OpenAPI contracts.

**Acceptance criteria**

- The web calls a versioned FastAPI endpoint; OpenAPI and Swagger show matching request/response shapes and an error example.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

### P01.5 — Create CI that builds both apps and runs contract, unit, and smoke checks

**Status:** In progress; [P01.5](https://github.com/spjyotiranjan/shipsense/pull/9). Maintained [local/CI commands](../docs/developer-setup.md#clean-integration-commands), [credential-free workflow](../.github/workflows/integration.yml), [existing diagnostic/integration tests](../scripts/integration-smoke.py) and [failure/recovery gates](../scripts/verify-integration-gates.py) are implemented. Local checks and four exact-head CI runs passed at `a9c4cd6`, independently cleared by Grace. The workflow/criteria revision needs current-head checks, independent delta review and acceptance; no separate hosted run/approval is a gate.
**Expected result:** Create CI that builds both apps and runs contract, unit, and smoke checks.

**Acceptance criteria**

- Clean credential-free PR/push CI performs frozen builds of both apps, quality/contracts/unit and actual API/built-web/browser diagnostics using the documented local commands.
- Retain existing integration tests and private hosted connection support where implemented; leave unsupported coverage explicit. No separate hosted-verification workflow/result or environment approval is required. Missing/invalid settings fail an explicitly requested real-connection test; they never count as passing live coverage.
- Configuration failures, owned-client cleanup and actual web-to-API success/failure/recovery are observable without disrupting hosted services.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_

## Phase kickoff — 8 November 2026

- Development tracking: P01.1–P01.5 checkpoints; historical kickoff administration is retired under Decision 0008.
- Corrected technical web/backend plans approved on 8 November 2026; bounded dependency adjustment recorded 9 November 2026. P01.1 and P01.2 accepted and merged; subsequent subphases retain their full technical gates.
