# ShipSense web

Next.js App Router and strict TypeScript own presentation and the web-facing backend layer. FastAPI owns canonical APIs, authorization, policy and provider integrations. No provider credentials or domain logic belong in browser code.

## Diagnostic boundary

The credential-free shell includes one client connection widget. `src/app/page.tsx` composes the page; `components/foundation-status.tsx` presents loading, connected and safe failure states. `lib/connection-check.ts` owns attempts, duplicate prevention and cancellation. The shared layout owns metadata, document language and the keyboard skip link. CSS preserves the simple responsive shell without external fonts, images or animation.

The browser calls only same-origin `GET /api/foundation`. Its server-only client calls canonical FastAPI `GET /api/v1/version`. Native runtime guards validate generated contract constraints, a 4 KiB response bound, exact fields and UTC freshness (at most 60 seconds old or five seconds ahead). Each hop uses no-store. There are no background retries. A five-second upstream deadline and seven-second browser deadline bound each attempt; cancellation and attempt identity suppress stale results.

Set server-only `SHIPSENSE_API_ORIGIN` to `http://127.0.0.1:8000` or `http://localhost:8000`. Other values fail closed with safe 502; redirects are refused. No request URL or header can select another upstream. A deployed origin requires a deployment configuration policy before extending this local allowlist. Server errors use canonical ApiError with web-only codes API_UNAVAILABLE/UPSTREAM_CONTRACT_INVALID (502) and API_TIMEOUT (504). Upstream bodies, addresses and exception traces are never exposed. Route logs contain only fixed route, status, opaque reference and duration.

## Reproduce from the repository root

Use exact pins in Decision 0005, `.node-version` and the root manifest. The single root lockfile is authoritative.

```sh
npm ci
npm run typecheck:web
npm run test:web
npm run build:web
npm run start --workspace apps/web -- --hostname 127.0.0.1
```

Start FastAPI using `services/api/README.md`, set the server variable above in the web process environment, and open `http://127.0.0.1:3000`. Stop with Ctrl+C. For development use `npm run dev --workspace apps/web`. No cloud account, backing service or secret is required. Missing configuration shows an unavailable state. Connected proves only API reachability; dependency readiness and customer health remain separate. Default API readiness remains safe503. Explicit external local configuration enables the separate [API-owned readiness probes](../../services/api/README.md); the web connection still reports version reachability only.

## Verification

Run `npm run quality`, `npm run test:foundation`, `npm run test:web` and `npm run build:web`. Native Node tests cover validation, safe failures, deadlines, duplicate requests, cancellation and late results. Start the production app and real API; check connection, stop API and retry, then restart and retry to prove recovery. Inspect loading/success/error at 320/768/1440 widths, enlarged text, keyboard skip/focus/Enter/Space, reduced motion, forced colors and no-JavaScript explanation. Keep disposable browser evidence outside the repository. The API readiness integration has separate real dependency stop/recovery tests; full seeded clean CI remains P01.5. Unchanged responsive/keyboard/degraded-state proof may be reused only with matching source/config/dependency hashes.
