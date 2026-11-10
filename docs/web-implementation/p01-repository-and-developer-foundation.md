# P01 web implementation plan — repository and developer foundation

## Current scope and prerequisites

The owner directed hosted-only MongoDB and Cloudflare R2 for application setup and integration on 10 November 2026. This replaces earlier emulator/container blueprints, fixture bootstraps and seed/reset requirements, including automated container fixtures. Preserve the chosen Next.js/TypeScript, FastAPI/Python, MongoDB, private R2 and Azure architecture. P01.1/P01.2 and historical P01.3/P01.4 acceptance remain revision-specific in [project status](../../PROJECT_STATUS.md). Historical proof does not establish current hosted compatibility or full P01 exit.

P01.1 establishes the web/API/worker/contracts/infra/docs/test boundaries; P01.2 pins npm/uv workspaces, one frozen lock per language, strict quality tools and generated contracts. Keep Decisions [0002](../decisions/0002-architecture-baseline.md), [0005](../decisions/0005-initial-foundation-toolchain.md), [0006](../decisions/0006-local-quality-toolchain.md) and [0008](../decisions/0008-checkpoint-development-workflow.md). Related checkpoint changes may share a PR; acceptance evidence remains separate. No development tracker validation is required.

## Hosted setup and shared contracts

Use existing hosted MongoDB and private Cloudflare R2 with the six server-only variables in placeholder-only [env.example](../../env.example). Local secrets remain ignored and are loaded explicitly by the API process. Validate required values, DNS endpoint policy, database/bucket scope and verified TLS before client creation. Use the pinned native async PyMongo and bounded off-loop Boto3 clients, fixed timeouts, small connection pools and limited retries. Cancellation retains occupied storage capacity until underlying work completes; shutdown drains only owned clients/workers. There is no local hosting or provisioning fallback.

P01.3 verifies authorized scoped MongoDB reads and private bucket access against supplied non-production hosted settings. The same-process bounded queue has no provider effects or durable/cross-process authority; retain duplicate, reordered, expired, poison, capacity and timeout cases. Inert reference manifests remain offline test inputs and are never seeded into hosted services. Public health reads do not enumerate or expose records, counts or provider errors. Tenant/project/service/environment/time/provider/version/freshness boundaries remain required as the domain API is built in P02/P03.

P01.4 exposes independent version/liveness/OpenAPI and safe readiness. Missing, malformed, denied or unavailable dependencies yield correlated no-store 503 while version/liveness and the web stay available. Production profiles remain refused for the foundation. Public errors/logs contain fixed safe messages and request references, never credentials, endpoint addresses, raw validation inputs or SDK exceptions. Keep the canonical OpenAPI byte check and generated TypeScript; avoid a second handwritten domain contract.

## P01.5 verification and CI

Use the [maintained commands](../developer-setup.md#clean-integration-commands) locally and in clean CI. Frozen bootstrap, aggregate formatting/lint/strict typing/offline secrets/contracts, meaningful API/shared utilities/web unit cases, Next.js production build and Python distributions remain required.

Credential-free pull-request/push CI runs real API/built-web/browser smoke. It checks default/malformed readiness 503, independent live/version 200, canonical version through Next.js, actual API stop/retry/restart recovery, safe errors and retained keyboard focus. A seeded contract-byte change and stopped upstream must fail the maintained success gates; restoring them must recover. No Docker, Compose, database emulator, service seed or teardown is involved. Installed Chrome/Chromium must be detected/versioned and compatible; fail on absence. Browser profiles and bounded sanitized evidence stay external; never reuse authenticated profiles or attach to existing browsers. Occupied loopback ports fail without killing other listeners; stop only test-owned processes.

Real hosted integration is a separate required live proof command using the same application settings. Missing/invalid configuration and denied/unavailable dependencies fail explicitly, with no skipped success. Verify scoped Mongo read, authenticated R2 bucket metadata, anonymous/wrong-key denial, actual API readiness 200 and built-web/browser API stop/retry/recovery without hosted service interruption or writes. Credential-free checks and mocked SDK failures do not prove live hosted compatibility or private-object policy. Keep deterministic SDK denial/timeout/cancellation/recovery tests without leaking their artificial errors.

Hosted CI is a manual workflow against a reviewed revision using a protected `hosted-integration` environment, restricted trusted branches and required reviewers. Secrets enter only its integration step, after installation/build. Pull requests receive none. Do not provision, migrate, seed, upload, reset, alter permissions or stop provider services. Preserve existing developer private state and volumes without lifecycle operations. Before live proof, supply authorized least-privilege test credentials privately; no credentials in source, artifacts, browser environment or prompts.

## Exit evidence and limits

Record revision/configuration, commands/results, affected checks, real behavior and limitations under each checkpoint. Required local checks/direct proof precede publication; clean current-head CI, independent exact-SHA review and acceptance follow. Preserve the Markdown pre-commit hook and full file/link/secret hygiene. A green build, merged PR or historical fixture acceptance alone never proves the phase complete.

Live MongoDB/R2 permissions, private-object policy, issuer/reference runtime, region/tier/residency/latency, costs and recurring-spend approval remain separate measured gates. No new model, cloud tier, provisioning or production effect is authorized. P02 owns authentication/tenancy/effective permission enforcement; P03 owns durable data, migrations, lifecycle/retention and evidence persistence. Do not add those features to make this foundation appear complete. Disclose the existing minimatch advisory and Starlette/httpx deprecation limits in project status.

## Web behavior

Next.js owns presentation and the backend-for-frontend. The browser uses the same-origin `/api/foundation` route; its server-only transport calls FastAPI with fixed origin, redirect refusal, bounded body/timeout, response schema validation and correlation. Only the API origin reaches the web server; MongoDB/R2 secrets never do. Connected indicates API reachability, not dependency readiness or customer recovery.

Keep loading/success/unavailable states, explicit retry, cleared stale success, disabled duplicate attempts and cancellation/late-result suppression. Preserve request-reference errors, keyboard focus, responsive layout and no-JavaScript behavior. Existing component tests cover malformed/oversized/slow/cancelled transport and stale attempts; direct browser smoke covers actual built UI success/failure/recovery. Keep the current simple functional UI; no redesign is part of P01.
