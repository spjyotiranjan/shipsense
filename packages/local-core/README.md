# Shared bounded adapters and synthetic test fixtures

Owns bounded private object I/O reused by hosted R2 readiness, explicitly isolated test-only Mongo/S3 clients, inert scoped fixture validation/conflict-preserving seed and the same-process no-effect queue. Production profiles refuse the foundation queue and synthetic clients. All clients require explicit async shutdown.

Application/developer setup uses hosted endpoints through [env.example](../../env.example) and the [API runbook](../../services/api/README.md); it does not start local storage. Only `npm run test:smoke` orchestrates synthetic containers for credential-free automated checks. The [fixture runbook](../../infra/local/README.md) describes ownership, private access, cancellation/cleanup and parity limits. `npm run test:local` covers safety/integrity/queue boundaries; `uv build --package shipsense-local` builds the shared package under the root lock. No automatic seed or hosted write is introduced.
