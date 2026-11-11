# P01 — Repository and developer foundation

**Scope update — 11 November 2026:** [Decision 0007 hosted-only amendment](../docs/decisions/0007-local-foundation-dependencies.md#hosted-only-integration-supersession--11-november-2026) replaces all self-hosted/container application, development and integration requirements. Use existing hosted MongoDB/private R2 through placeholder-only [.env.example](../.env.example). Credential-free PR checks and protected manual hosted job in Integration integration use the [same commands](../docs/developer-setup.md#clean-integration-commands). Historical local acceptance remains revision-specific; configuration has been supplied; local/remote outcomes and full P01 exit require actual verification. MongoDB uses a validated `{base}-{profile}` target, hosted dependencies are unconditional, and one Integration workflow contains credential-free diagnostics plus its manual protected hosted job.

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

**Status:** In progress for current hosted proof. Author local hosted read/private-authentication checks and API/web/browser recovery passed on 11 November ([PR #9](https://github.com/spjyotiranjan/shipsense/pull/9)); protected remote proof, independent current-SHA review and acceptance remain pending. Historical synthetic core was accepted at `c441de1` on 9 November 2026 ([source PR #7](https://github.com/spjyotiranjan/shipsense/pull/7)); its merge and hosted compatibility are separate facts. The self-hosted implementation is retired by the newer owner direction.

**Implementation:** [Hosted settings/clients](../services/api/src/shipsense_api/hosted.py), [API configuration](../services/api/README.md), [bounded shared storage](../packages/local-core/src/shipsense_local/adapters.py), [same-process queue](../packages/local-core/src/shipsense_local/queue.py), [SDK/config/lifecycle tests](../services/api/tests/test_hosted.py) and [shared utility tests](../packages/local-core/tests/test_unit.py).

**Acceptance criteria**

- A new developer supplies existing hosted settings privately using the placeholder-only example and documented command; no database/storage installation, container or seed is required.
- Strict server-only configuration, verified TLS and bounded clients enforce database/bucket scope. Missing/invalid values keep readiness 503 without preventing independent live/version/web diagnostics; public errors/logs hide secrets and endpoints.
- A bounded read-only integration against authorized non-production MongoDB/R2 proves scoped read, authenticated bucket access and anonymous/wrong-key authentication rejection using a zero-key request. It performs no schema/seed/object writes, provisioning or provider disruption; local and protected remote outcomes are recorded separately.
- Queue tests preserve duplicate/reorder/poison/expiry/timeout/capacity/no-effect behavior. Client tests cover deadlines, cancellation, denial/recovery, partial construction and draining shutdown.

**Proof to attach:** Current revision, profile and local/remote hosted results under this checkpoint. Missing access is an explicit remaining gate; mocked SDK success or historical emulator proof is insufficient.

### P01.4 — Build Next.js shell and FastAPI health/version endpoints; document Swagger/OpenAPI contracts

**Status:** Complete; accepted 9 November 2026 at `94279641cf4660b4a991db7af8c69b5e54b1a889`, stacked base `c441de1`. [Source PR](https://github.com/spjyotiranjan/shipsense/pull/8), [exact-revision independent clearance](https://github.com/spjyotiranjan/shipsense/pull/8#issuecomment-6744104125); PR #8 remains unmerged. Credential-free PR #6 remains merged.
**Implementation:** [canonical API](../services/api/src/shipsense_api/main.py), [bounded readiness interface](../services/api/src/shipsense_api/diagnostics.py), [contract/failure tests](../services/api/tests/test_diagnostics.py) and [generated OpenAPI](../packages/contracts/openapi.json). Default startup exposes version/liveness/schema without backing services and keeps readiness503. Historical external local configuration enabled [owned real Mongo/S3 and same-process queue](../services/api/src/shipsense_api/readiness_runtime.py). [Real integration tests](https://github.com/spjyotiranjan/shipsense/blob/94279641cf4660b4a991db7af8c69b5e54b1a889/services/api/tests/test_readiness_integration.py) and direct HTTP proof exercise configured200, separate Mongo/storage200-to-503-to-200 with live/version/web remaining200, bounded storage deadlines/capacity/cancellation, queue unavailable/recovery and clean restart/shutdown. [Configuration/lifecycle tests](../services/api/tests/test_hosted_lifespan.py) cover invalid/missing/foreign configuration and redaction. Public OpenAPI is unchanged. Local/direct proof, exact-current-revision independent clearance, required remote checks and acceptance passed; P01.4 completion is separate from PR #8 landing and full P01 exit.
**Implementation prerequisite:** tested accepted P01.1/P01.2 supports credential-free canonical version/liveness/safe-error contracts and subsequent web diagnostic integration without P01.3.
**Current hosted acceptance prerequisite:** P01.3 authorized hosted adapters and read-only local/remote compatibility proof, safe configuration failure and local-owned API stop/retry/recovery. Preserve historical revision-bound acceptance without requiring new container or remote-service outages.
**Web implementation:** [diagnostic UI](../apps/web/src/components/foundation-status.tsx), [same-origin route](../apps/web/src/app/api/foundation/route.ts), [bounded transport](../apps/web/src/lib/server/api-transport.ts) and [failure/race tests](../apps/web/tests/diagnostics.test.ts). Run the [web reproduction and verification commands](../apps/web/README.md). Safe transport errors share the generated canonical envelope. Connected indicates API reachability only. Full readiness and phase exit remain unverified.
**Expected result:** Build Next.js shell and FastAPI health/version endpoints; document Swagger/OpenAPI contracts.

**Acceptance criteria**

- The web calls a versioned FastAPI endpoint; OpenAPI and Swagger show matching request/response shapes and an error example.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence under the checkpoint in `../PROJECT_STATUS.md` and the relevant pull request.

### P01.5 — Create CI that builds both apps and runs contract, unit, and smoke checks

**Status:** In progress; [P01.5](https://github.com/spjyotiranjan/shipsense/pull/9). Maintained [local/CI commands](../docs/developer-setup.md#clean-integration-commands), [workflow](../.github/workflows/integration.yml), [credential-free diagnostics and hosted integration](../scripts/integration-smoke.py) and [failure/recovery gates](../scripts/verify-integration-gates.py) are implemented. Revised hosted-only local checks and actual read-only local hosted/browser recovery proof pass; protected remote proof, independent current-SHA review and acceptance remain delivery gates; historical container results do not cover this revision.
**Expected result:** Create CI that builds both apps and runs contract, unit, and smoke checks.

**Acceptance criteria**

- Clean credential-free PR/push CI performs frozen builds of both apps, quality/contracts/unit and actual API/built-web/browser diagnostics using the documented local commands.
- The same hosted integration command passes locally and in a protected manually invoked workflow on reviewed code with dedicated non-production read-only settings. Missing settings or access failures must fail explicitly.
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
