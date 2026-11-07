# Decision 0005 — Initial foundation toolchain

**Date:** 8 November 2026
**Status:** Accepted for initial local foundation implementation; compatibility proof remains a delivery gate.
**Decision owner:** Patrick Jane, within delegated technical authority.

## Decision

Use npm workspaces with one root package-lock.json for the JavaScript packages and uv workspaces with one root uv.lock for the Python services. Pin direct dependencies and runtime/tool versions; reproduce installs with npm ci and uv sync --frozen. Keep Python virtual environments and generated build output untracked.

Initial local pins: Node 26.7.0, npm 11.19.0, Python 3.14.7, uv 0.12.21, FastAPI 0.162.2, Uvicorn 0.54.0, Pydantic 2.14.3, Hatchling 1.33.0, httpx 0.28.1, Next.js 16.4.5 and openapi-typescript 7.13.0. These are accepted starting pins, not a claim of verified runtime compatibility. Initial web pins additionally accepted on 8 November 2026: React and react-dom 19.3.1, TypeScript 5.9.3, @types/react and @types/react-dom 19.3.0, and @types/node 26.6.6, from the joint web proposal recorded in PAT-106 comment f0d0f35b-ffc0-4cd7-a470-6165ec482ac0. These are starting pins subject to the same compatibility gate.

FastAPI owns the canonical generated OpenAPI artifact. Generate TypeScript from that artifact; do not create a second handwritten domain API. A minimal local contract is sufficient for the repository boundary; full health/version integration and diagnostic failure states remain P01.4. Runtime response validation is still required where external responses enter the web layer.

## Rationale and limits

One resolver and lock per language keeps independently buildable packages reproducible without adding orchestration infrastructure. The choices preserve Decisions 0001–0003 and the accepted phase plans. Registry engine ranges are preliminary evidence; frozen install, service build/import/startup, web build/startup and deterministic contract generation/consumption must pass in the supplied primary checkout before commit/push/PR. Record exact tested versions and limitations. If compatibility fails, retain the failure evidence and return a concrete replacement proposal for acceptance rather than silently changing pins or the stack.

This decision authorizes credential-free local foundation work only. It selects no local issuer, service emulator, Astronomy Shop service/revision, production hosting runtime, region, tier or spending amount. Full quality tooling remains P01.2, with issuer/reference/region/cost gates retained for P01 exit.

## Sources

- Decisions 0001–0003 and the accepted P01 web/backend implementation plans.
- Tool proposal: PAT-104 comment c4dfed0b-2eea-4503-83e5-97b25c199f81; accepted by Patrick on 8 November 2026.
- [uv workspace documentation](https://docs.astral.sh/uv/concepts/projects/workspaces/).
- [Next.js installation documentation](https://nextjs.org/docs/app/getting-started/installation).
- [Node.js release policy](https://nodejs.org/en/about/previous-releases).
