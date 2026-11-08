# ShipSense web

Next.js App Router and strict TypeScript own presentation and the web-facing backend layer. FastAPI owns canonical domain APIs, authorization, policy and provider integrations. Workers own asynchronous processing. No provider credentials or domain logic belong in browser code.

## SCRUM-13 boundary

The root route is a static, credential-free developer foundation shell. It deliberately reports no connected API or evaluated service health. There are no external requests, customer records, authentication claims or production controls. Health/version fetching, runtime validation, loading/error/retry states and same-origin API integration are SCRUM-16 work. A successful page load is not evidence of customer recovery.

The server component owns static content; the shared layout owns metadata, document language and the keyboard skip link. CSS handles responsive layout without client state, external fonts, images or animation. No custom client bundle is introduced.

## Reproduce from the repository root

Use the exact runtime and dependency pins in Decision 0005, `.node-version` and the root package manifest. The single root lockfile is authoritative; do not install separately inside this folder.

```sh
npm ci
npm run typecheck:web
npm run build:web
npm run start --workspace apps/web -- --hostname 127.0.0.1
```

Open `http://127.0.0.1:3000`. Stop with Ctrl+C. For development use `npm run dev --workspace apps/web`. No environment variables, API process, cloud account or secrets are required for this slice. Missing upstream configuration cannot produce a misleading connected state because this page does not attempt a connection.

## Verification

Check the production build/startup, root HTTP response and a missing route. Inspect at mobile, tablet and desktop widths, including enlarged text, keyboard skip navigation, visible focus, heading/landmark structure, contrast and no horizontal overflow. No loading/error controls exist in this static slice. Full lint/format/secret gates follow in SCRUM-14.
