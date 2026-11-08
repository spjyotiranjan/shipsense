# Synthetic fixtures boundary

Owns inert test inputs, provenance and expected outcomes. `foundation.json` is a bounded, scoped, missing-evidence fixture. It contains no customer records, secrets, instructions for tools or executable payload. Its historical times and missing freshness are deliberate; they must never be presented as current evidence.

Run `python scripts/validate-foundation.py` from the root. A missing file fails with `FIXTURE_MISSING`; malformed or unexpected fields fail closed without printing input. The validator performs no ingestion, provider call or persistence. Full manifests, checksums, expiry, named fault scenarios and idempotent local seeding arrive in P01.3.
