# P01 web implementation plan — repository and developer foundation

**Status:** P01 technical development plan, revised 9 November 2026. Technical selections identified as proposals remain unresolved until validated and recorded.

Read with the [backend plan](../backend-implementation/p01-repository-and-developer-foundation.md), [P01 acceptance criteria](../../Phases/P01-repository-and-developer-foundation.md), [roadmap](../../ROADMAP.md), [status](../../PROJECT_STATUS.md), and accepted Decisions [0001](../decisions/0001-release-1-scope.md), [0002](../decisions/0002-architecture-baseline.md), [0003](../decisions/0003-jira-owned-development-validation.md). The product source remains [the specification](../shipsense-full-product-specification.pdf); accepted decisions define the architecture baseline.

## Tested foundation and remaining dependency gates

P01.1/SCRUM-13 and P01.2/SCRUM-14 are accepted and merged on 9 November 2026: [foundation proof](https://spjyotiranjan.atlassian.net/browse/SCRUM-13?focusedCommentId=10003), [quality proof](https://spjyotiranjan.atlassian.net/browse/SCRUM-14), [PR #4](https://github.com/spjyotiranjan/shipsense/pull/4), and [PR #5](https://github.com/spjyotiranjan/shipsense/pull/5). Main baseline is `7749e4de360372f6d99f6b468c8fcbf22f7a4947`. Reuse accepted foundation/quality proof; neither acceptance nor merge completes P01.

Tested surfaces include the credential-free FastAPI `/foundation` route, generated canonical OpenAPI and TypeScript consumption, minimal web shell, frozen npm/uv workspaces and byte-level contract drift/quality checks. Version/liveness/readiness/error contracts, runtime response validation and diagnostic UI states below are remaining SCRUM-16 work, not existing behavior.

SCRUM-16 contract and web diagnostic implementation requires accepted SCRUM-13/14 surfaces, without waiting for SCRUM-15 storage/queue setup. First implement and verify canonical version/liveness/safe-error schemas and generated contracts without cloud credentials; then integrate the web against that tested contract. Schema generation, version and liveness must remain independent of storage, queue and database availability. Readiness schema/error examples and bounded probe interfaces can be defined now, but full SCRUM-16 acceptance requires SCRUM-15's real local adapters, seeded dependencies and outage/recovery proof. Stubs or mocked readiness cannot satisfy that gate.

SCRUM-15 still requires validated issuer/emulator/reference-service selections and its fixture/region/tier/cost proof. SCRUM-17 full clean-checkout build/unit/contract/smoke CI depends on completed SCRUM-15/16 integration. Full readiness and P01 exit retain every positive, negative and recovery criterion; this dependency split waives none.

Accepted tooling is recorded in Decisions [0005](../decisions/0005-initial-foundation-toolchain.md) and [0006](../decisions/0006-local-quality-toolchain.md). Preserve the current pins and frozen locks; select only still-missing tools with compatibility proof. The development minimatch advisory remains a disclosed limitation: recorded triage found no reachable vulnerable path in the current lint configuration, not blanket risk acceptance. Starlette/httpx deprecation remains. Decision 0003's 100-commit ceiling and unverified PR creation/title-edit/new-push lifecycle remain unproven; do not treat that status as a required merge gate until verified. OpenAI model selection remains advisory until measured P12 evaluation; no model is selected by this plan.

## Subphase dependencies

P00 architecture decisions are the prerequisite. Dependencies follow tested surfaces, not whole-ticket sequencing; SCRUM-15 and the credential-free SCRUM-16 slice can proceed independently after accepted SCRUM-13/14.

| Order | Subphase | Deliverable and dependency proof |
| --- | --- | --- |
| 1 | P01.1 / SCRUM-13 | Seven repository boundaries, package responsibility READMEs and repeatable minimal builds |
| 2 | P01.2 / SCRUM-14 | Pinned toolchains, frozen locks, format/lint/type/secret checks with seeded local and CI failures |
| 3 | P01.3 / SCRUM-15 | Credential-free local services, scoped synthetic fixtures, idempotent seed and dependency failure proof |
| 4 | P01.4 / SCRUM-16 | After accepted SCRUM-13/14: credential-free FastAPI contracts, then web diagnostics; SCRUM-15 required for full readiness/outage/recovery acceptance |
| 5 | P01.5 / SCRUM-17 | Clean CI repeats local contract/unit/smoke checks and builds both applications |

## Web boundary and tooling proposal

Keep a simple, consistent functional UI; the user deferred a full redesign until broad product coverage. Use Next.js and strict TypeScript. Python FastAPI is the main backend. Next.js API routes are the web-facing backend layer and call FastAPI for canonical domain behavior.

| Path | Responsibility |
| --- | --- |
| `apps/web/src/app/page.tsx` | Foundation diagnostic shell; initial loading and completed/error states |
| `apps/web/src/app/api/foundation/route.ts` | Same-origin web-facing backend; fixed upstream API destination, bounded request and safe error mapping |
| `apps/web/src/components/foundation-status.tsx` | Presentational status/retry component; no provider logic |
| `apps/web/src/lib/server/api-client.ts` | Server-only typed FastAPI client and runtime response validation |
| `apps/web/tests/` | State rendering and browser smoke checks |
| `packages/contracts/` | FastAPI-generated OpenAPI, typed client/schema artifacts and generation instructions |
| `docs/` | Boot, developer commands, technical plans and evidence links |

No MongoDB, R2, queue, provider SDK or domain authorization implementation in the browser or web layer. FastAPI owns canonical APIs. Browser-visible configuration is limited to intentionally public values; upstream origins and any future session credentials remain server-only. Do not add arbitrary URL proxying, user-controlled upstream headers or fetch destinations.

Use the accepted npm/uv workspaces, one frozen lock per language, generated OpenAPI/TypeScript and pinned quality tools from Decisions 0005/0006. Their compatibility and seeded failure/recovery proof are accepted under SCRUM-13/14; preserve those pins. Still-missing runtime response validation, browser smoke tooling and emulators require explicit compatibility evidence before use. Do not add a second handwritten domain API, floating versions or duplicate locks. Document additions and regeneration commands without repeating accepted foundation work.

## First vertical slice and interface

The first screen reports ShipSense API reachability/version for local development. It does not display tenant/customer data, login, provider controls or deployment health. Keep the purpose visible: a reachable API says nothing about customer recovery. P02 supplies authenticated product surfaces later.

```text
ShipSense — developer foundation
Local development · synthetic data only

API connection: Checking… / Connected / Unavailable
API version: 0.1.0-dev (only after validated success)
Last checked: <local display of returned UTC time>
[Retry connection]
Request reference: <safe opaque correlation ID on failure>
```

Use semantic heading/main, text labels as well as icons/colors, readable contrast, visible keyboard focus, a button with an accessible name, and polite status announcements. Disable duplicate retries while in flight without trapping focus. On failure clear the current version field; if showing a previous result, label it explicitly as historical with its timestamp. Use the same compact layout on mobile and desktop. Loading, invalid/missing response, disconnected/timeout and recovered states require proof. A shell without scoped records does not need fake tenant selectors or fabricated denied-data counts.

```mermaid
sequenceDiagram
  participant U as Browser
  participant W as Next.js web backend
  participant A as FastAPI
  U->>W: GET /api/foundation
  W->>A: GET /api/v1/version (fixed origin, correlation)
  A-->>W: 200 VersionResponse or typed error
  W->>W: Validate response and redact unexpected failures
  W-->>U: 200 validated response / safe 502 or 504
  U->>U: Render matching accessible state
```

The [backend plan](../backend-implementation/p01-repository-and-developer-foundation.md#api-contract-proposal) defines canonical schemas. Proposed success body, shared without a second domain shape:

```json
{"service":"shipsense-api","version":"0.1.0-dev","apiVersion":"v1","observedAt":"2026-11-08T00:00:00Z"}
```

Proposed safe web-backend error:

```json
{"error":{"code":"API_UNAVAILABLE","message":"The API is unavailable. Retry the connection.","requestId":"req-local-001","retryable":true}}
```

| Condition | Web backend result | UI behavior |
| --- | --- | --- |
| Valid canonical success | 200; `Cache-Control: no-store` | Show Connected, version and checked time |
| API network failure or invalid schema | 502 `API_UNAVAILABLE` or `UPSTREAM_CONTRACT_INVALID` | Clear current success; retry available; opaque request reference |
| Bounded upstream timeout | 504 `API_TIMEOUT` | Show timeout text; explicit retry, no endless spinner |
| Future 401/403 | Preserve safe auth semantics; never reinterpret as success | P02 login/denied state; no resource metadata in error |

Propose a 5-second upstream deadline and one explicit request per user attempt, with cancellation on unmount and no background retry loop. Validate returned strings, timestamps and size; do not render returned HTML. Treat response/log content as untrusted. Request references are bounded opaque identifiers, never credentials. Record request ID, route, status and elapsed time in safe structured server logs; exclude bodies, tokens and upstream error traces from browser responses.

Do not cache this diagnostic across users or environments. Cancel superseded requests or use attempt IDs so a slow failed request cannot overwrite newer success. No optimistic Connected state. Keep upstream connection pooling server-side with bounded timeouts; do not fetch MongoDB/R2/queue on every render. A single version request proves the required web-to-API path. Readiness remains a separate operator check. If later scoped reads are introduced, require API-side effective permission resolution first, and include authorized scope/version/freshness in cache design before enabling caching.

## Local and CI verification plan

The change surface includes Next.js runtime, server fetch, canonical schema artifacts, UI state and shared toolchain. Runtime integration and contract changes need more than a compile. Use only the primary checkout. The backend plan defines proposed common command targets; implement and document those exact commands or revise both plans together before work depends on them.

1. Record the tested revision, config profile, tool versions and dependency availability. No cloud credentials or real tenant data may be needed.
2. Frozen install and generated-contract drift check; format/lint/type/unit checks and production Next.js build. Configure the existing Markdown hook with `core.hooksPath=.githooks`. Test files and commands remain understandable from READMEs.
3. For the credential-free SCRUM-16 slice, boot FastAPI and the built web app without MongoDB/queue/storage; browser smoke must observe a real Next.js-to-FastAPI response and match `/api/v1/version` to displayed version. A mocked response alone cannot pass. After SCRUM-15, repeat integrated smoke with seeded local dependencies and prove readiness dependency-outage/recovery while liveness remains 200; this is required before full SCRUM-16 acceptance.
4. Stop the API, retry and observe a safe unavailable state; inject delayed/malformed responses through a local test harness to verify timeout/schema errors and stale-attempt suppression. Restart API and prove recovery. Check logs/browser for secret or stack-trace leakage.
5. Run keyboard navigation and inspect loading/success/error at narrow and wide viewports; capture screenshots with expected/observed result. Component tests can deterministically cover loading and cancellation races.
6. P01.5 CI uses the same targets, pinned tools and synthetic services; installs/builds both apps from a clean checkout, then runs real browser smoke. Make API failure cause smoke to fail. Publish sanitized logs and screenshots under bounded artifact retention.

For SCRUM-14, seed format, lint, type and synthetic-secret violations independently in disposable test inputs; each must make its local check and CI check fail, then pass after removal. Never commit a real secret or a deliberately broken product. Jira owns remote development-key checks under Decision 0003; do not resurrect removed local key hooks or duplicate Actions validators. Its documented lifecycle gaps remain explicit acceptance risks, not assumed green checks.

## Phase exit proof

Attach reproducible proof for each subphase: commands with exit codes, tested revision and configuration, generated API artifact, direct behavior results, screenshots where applicable, failure/recovery proof and remaining gaps. All five subphase criteria must pass. The final phase record includes review date, evidence links, unresolved risks and an explicit technical verdict. P02 depends on this complete P01 exit proof.

## Outstanding technical selections

- Local OIDC issuer and the pinned Astronomy Shop service/revision/fixtures are not yet selected; the backend plan defines evaluation criteria. Resolve them in P01 without claiming P02 authentication is complete.
- Region, Atlas tier, residency, latency, monthly forecast, quota/alert values and recurring-spend approval remain gates before paid provisioning. The diagnostic UI needs no cloud credentials.
- Preserve accepted tooling pins and generated TypeScript method from Decisions 0005/0006; any added runtime validator/browser runner and proposed diagnostic/error contracts require compatibility and contract validation before dependent code. API health data remains separate from customer health claims.
- Keep the UI simple and consistent. Verify concrete accessibility and usability uncertainties in the diagnostic journey.
