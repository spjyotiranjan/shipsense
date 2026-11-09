# Synthetic fixtures boundary

Owns inert test inputs, provenance and expected outcomes. `foundation.json` is a bounded, scoped, missing-evidence fixture. It contains no customer records, secrets, instructions for tools or executable payload. Its historical times and missing freshness are deliberate; they must never be presented as current evidence.

Run `python scripts/validate-foundation.py` from the root for the original foundation input. A missing file fails with `FIXTURE_MISSING`; malformed or unexpected fields fail closed without printing input. The validator performs no ingestion, provider call or persistence.

`p01/` contains six bounded inert manifests and JSON payloads: pipeline failure, probe/config regression, missing telemetry, dependency failure, injected runbook and deployment regression. Provenance pins Astronomy Shop product-catalog 3.1.0 and its exact revision. Each manifest carries full synthetic scope, UTC event/observed/expiry times, explicit freshness and outcome, correlation and a checked payload SHA-256. They are constructed synthetic cases, not captured live provider evidence or completed AI evaluations. Injection text remains inert. Times are historical inputs, not current health observations.

The [local runbook](../../infra/local/README.md) explains explicit idempotent seeding, object-before-metadata integrity, concurrent conflicts and safe reset. `npm run test:local` validates all six without dependencies. Integration proof requires actual owned Mongo/S3 and the explicit state directory.
