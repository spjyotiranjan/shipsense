# Isolated automated test fixtures

Application/developer setup uses existing hosted MongoDB and private Cloudflare R2 through root [env.example](../../env.example) and the [API runbook](../../services/api/README.md). No self-hosted database or storage is required for application startup. Decision 0007's [hosted setup amendment](../../docs/decisions/0007-local-foundation-dependencies.md#hosted-mongodb-and-cloudflare-r2-application-setup--10-november-2026) supersedes the historical manual local setup. Public npm startup/seed/reset aliases have been removed.

The files here remain solely for credential-free automated tests. `npm run test:smoke` orchestrates an isolated synthetic Mongo/private S3 attempt, explicit seed, real API/built-web/browser outage/recovery and cleanup. Test configuration explicitly selects `SHIPSENSE_DEPENDENCIES=test-fixtures`; hosted validation never permits its plaintext loopback exceptions. No hosted credential is read or sent by this gate. Run it only within an exclusive test runtime window; see [requirements and commands](../../docs/developer-setup.md#clean-integration-commands).

## Ownership and private access

Only pinned Decision 0007 image digests and frozen clients are used. The fixed `shipsense-ci-p01` namespace has new external owner-only state and attempt credentials; it cannot adopt existing resources. Repository/state identity, exact names, labels, daemon, loopback ports and memory thresholds are checked before effects. Ambiguous ownership or occupied ports cause refusal. No global prune, orphan removal, listener termination or host changes occur. Cleanup validates the attempt and removes only its synthetic CI containers/network/volumes/private files. Existing `shipsense-local-p01` volumes and private state are preserved, never reset by CI.

Mongo's application identity is limited to `shipsense_fixture_p01`. Root bootstrap inputs remain private on the host and are copied only to bounded container tmpfs with directory0700/files0600, owned by mongodb, before the official privilege drop. The S3 root wrapper stages only the host-validated identity into a separate1MiB tmpfs, seaweed-owned directory0700/file0600, verifies the source/copied digests and execs the unchanged pinned privilege-dropping entrypoint. Only the expected digest enters fixture environment, never credentials; neither config nor digest is logged. Invalid/missing/oversized/unreadable input, malformed/mismatched digest or unavailable tmpfs refuses startup before service launch. S3 has one nonanonymous identity restricted to the fixture bucket; application credentials cannot create buckets or administer storage. Actual unsigned/wrong-key/wrong-bucket denial is required. Mongo37017/S3 38333 are loopback-only; control ports are unpublished. Containers share a dedicated bridge; this does not prove outbound denial.

## Integrity and no-effect queue

Six inert manifests pin Astronomy Shop product-catalog3.1.0 and retain scope, UTC times, freshness, provenance and hashes. Injection text is inert. Seed is explicit inside the test attempt, writes checksum-addressed objects conditionally before metadata and preserves conflicting evidence. Repeated identical seed is a no-op. Concurrency, missing/corrupt objects and interrupted retry are tested. No migration or seed targets a hosted endpoint.

The bounded queue and consumer share one process and execute no provider effects. Duplicates, reordered, poison and timed-out work are tested. Restart loses messages/deduplication state; no Service Bus durability or cross-process parity is claimed.

## Failure and recovery

The smoke requires real tests with no skipped integration success. It proves default503, explicitly configured fixture200, separate real dependency200-to-503-to-200, liveness/version independence and browser API stop/retry/recovery. Bounded S3 capacity is retained after caller cancellation until actual work ends. Shutdown drains owned clients/workers. Failure/cancellation invokes ownership-checked cleanup; CI repeats it on every outcome. If interrupted, use the original external `SHIPSENSE_EVIDENCE_DIR` with:

```sh
uv run --frozen --package shipsense-api python scripts/verify-integration-gates.py --cleanup
uv run --frozen --package shipsense-api python scripts/integration-smoke.py --cleanup
```

Never delete unknown resources to make tests pass. Historical accepted local-profile results remain identified by revision; neither those nor the test emulators prove hosted MongoDB/Cloudflare R2 compatibility, permissions, private bucket policy, lifecycle, recovery, capacity or production security. Issuer/reference, region/tier/residency/cost and P01 exit retain separate gates.
