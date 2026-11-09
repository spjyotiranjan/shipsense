# API contracts boundary

Owns the generated canonical FastAPI OpenAPI artifact and derived TypeScript. From the root run `npm run contracts:generate` after frozen npm/uv installation, then `npm run contracts:check`. `src/consumption.ts` proves response consumption by indexed generated type. Regenerate twice and compare file hashes to check deterministic output; inspect contract changes alongside API edits.

Do not hand-edit `openapi.json` or `src/generated.ts`. Generated contracts include the local version/liveness/readiness endpoints and safe validation/internal/dependency error envelopes. `src/consumption.ts` exports the indexed version and error response types for web consumers. This package creates no web fetch or domain API. Runtime validation of upstream responses at the web boundary remains required: TypeScript alone does not validate external data. A readiness schema does not establish real dependency availability.
