# ShipSense API

FastAPI owns the canonical API. Next.js owns the web-facing backend and calls this API. OpenAPI is generated into `packages/contracts/openapi.json`; Swagger is available at `/docs`.

## Hosted configuration

Copy the placeholder-only [.env.example](../../.env.example) to ignored `.env.local`. Load it explicitly with `uv run --env-file .env.local --frozen --package shipsense-api uvicorn shipsense_api.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log`.

| Setting                          | Required value                                                                                                              |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `SHIPSENSE_MONGODB_URI`          | Existing authenticated hosted `mongodb+srv://` or `mongodb://` URI; TLS certificate and hostname verification are mandatory |
| `SHIPSENSE_MONGODB_DATABASE`     | Database base; target is `{base}-{profile}`, at most 63 bytes; never admin/config/local                                     |
| `SHIPSENSE_R2_ENDPOINT`          | Private account S3 endpoint `https://<account-id>.r2.cloudflarestorage.com` (EU/FedRAMP endpoint variants supported)        |
| `SHIPSENSE_R2_BUCKET`            | Existing private application bucket                                                                                         |
| `SHIPSENSE_R2_ACCESS_KEY_ID`     | Bucket-scoped S3 access key                                                                                                 |
| `SHIPSENSE_R2_SECRET_ACCESS_KEY` | Corresponding secret key                                                                                                    |

The foundation uses `SHIPSENSE_PROFILE=local` (the local API process, with hosted dependencies). The profile defaults to `local`; production and unsupported profiles remain refused. MongoDB selects exactly `{SHIPSENSE_MONGODB_DATABASE}-{SHIPSENSE_PROFILE}` without removing an existing suffix; for example `shipsense` selects `shipsense-local`. The final name must fit 63 bytes. Hosted MongoDB/private R2 is the sole dependency path; no selector is required. The API never provisions, seeds or resets a database or bucket. No fallback service or external private-state directory is loaded. Credentials stay server-only; never use `NEXT_PUBLIC_` settings or send them to Next.js/browser processes.

`/health/live` and `/api/v1/version` are credential-free. `/health/ready` returns safe correlated/no-store 503 for missing/invalid/denied/unavailable dependencies and 200 only when bounded Mongo read, private R2 access and same-process queue probes succeed. Public errors/logs hide addresses, credentials and exception details. Clients use verified TLS, small pools, fixed deadlines, limited retries and draining shutdown. The queue has no provider effects or durable/cross-process authority.

## Verification

Run `npm run test:foundation`, `npm run test:unit`, `npm run build` and the [documented smoke/integration commands](../../docs/developer-setup.md#clean-integration-commands). Hosted integration performs only a scoped read and bucket metadata checks. Missing credentials fail the hosted command; credential-free smoke remains separately named and does not claim hosted readiness. Unexercised live permissions, private-object policy and production parity remain explicit coverage limitations. A separate hosted-verification result or environment approval is not a P01.3/P01.5 acceptance gate.
