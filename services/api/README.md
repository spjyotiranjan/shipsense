# Canonical API boundary

Owns canonical APIs, authorization, integrations and orchestration. This local-only skeleton exposes public `GET /foundation` with no customer data. Domain authorization arrives in P02; no permissive authorization middleware is installed. Health/version/readiness behavior is P01.4.

From the root: `uv sync --frozen --all-packages --all-groups`; `uv build --package shipsense-api`; `uv run --frozen --package shipsense-api uvicorn shipsense_api.main:create_app --factory --host 127.0.0.1 --port 8000`. Inspect `/foundation`, `/docs` and `/openapi.json`. No credentials or backing service are required. `SHIPSENSE_PROFILE` defaults to `local`; any other profile fails startup without exposing its value. Stop with Ctrl+C.

Run `npm run test:foundation` for local diagnostic, unsupported profile and fixture failure tests. Run `npm run contracts:generate` to publish the canonical schema and generated TypeScript. No migrations or persistence exist in this slice.
