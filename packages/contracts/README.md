# API contracts boundary

Owns the generated canonical FastAPI OpenAPI artifact and derived TypeScript. From the root run `npm run contracts:generate` after frozen npm/uv installation, then `npm run contracts:check`. `src/consumption.ts` proves response consumption by indexed generated type. Regenerate twice and compare file hashes to check deterministic output; inspect contract changes alongside API edits.

Do not hand-edit `openapi.json` or `src/generated.ts`. This minimal local contract creates no web fetch or domain API. P01.4 adds version/health and runtime validation of upstream responses at the web boundary. TypeScript alone does not validate external data.
