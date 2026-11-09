# Synthetic local services

This profile implements the bounded core from [Decision 0007](../../docs/decisions/0007-local-foundation-dependencies.md). It requires the pinned repository tools, Docker with a local Linux/amd64 engine, and Docker Compose (verified with 5.5.1). Install the frozen workspace first:

```sh
npm ci
uv lock --check
uv sync --frozen --all-packages --all-groups
npm run local:up
npm run fixtures:seed
npm run fixtures:seed
npm run local:check
npm run queue:smoke
npm run local:down
```

The second seed reports six unchanged records. Startup and seeding are separate commands. No cloud credentials, issuer, reference topology or production effects are used. Run from the repository root in PowerShell or a POSIX shell. The runtime reads no host AWS credentials/profiles; the two selected container digests and the single Python lock are frozen. Docker and package registry downloads require network access on first use.

Credentials and ownership state default to `%LOCALAPPDATA%/ShipSense/local-p01` on Windows or `~/.local/state/ShipSense/local-p01` on POSIX. Every command accepts `--state-dir` after npm's `--` separator, for example `npm run local:up -- --state-dir /private/external/shipsense-state`. Use the **same external directory** for every command. The directory is private to the current OS account; credentials never belong in this repository, shell arguments, screenshots or logs. Preserve it together with its volumes. Initialization refuses an existing incomplete directory rather than replacing credentials. Do not print `local.json`, `s3.json`, Mongo bootstrap files, or raw Docker/client diagnostics.

## Isolation and lifecycle

The fixed project is `shipsense-local-p01`; its dedicated bridge separates these services from unrelated container networks. Only Mongo `127.0.0.1:37017` and S3 `127.0.0.1:38333` are published. All admin/filer/gRPC/metrics ports remain unpublished. This bridge is not an outbound firewall: Docker's `internal` flag suppresses the required host port publishing on the verified engine. No host network/daemon setting is changed. Never expose this profile to a LAN or use real customer data.

Mongo uses a root bootstrap file and a separate application identity limited to `shipsense_fixture_p01`. The S3 configuration has exactly one nonanonymous identity with Read/Write/List restricted to `shipsense-fixtures`. The container precreates that one bucket; application credentials cannot create buckets or use Admin. IAM, WebDAV, admin UI, Iceberg/Lance and telemetry are disabled. `local:up` requires successful authenticated operations and explicit HTTP 403 for unsigned, incorrect-key and wrong-bucket requests before reporting ready. Missing, empty or changed identity configuration is refused before startup.

Initial limits are Mongo 768 MiB (256 MiB WiredTiger cache), storage 512 MiB, one CPU and 128 PIDs each. Startup measures available host memory, requires at least 1.5 GiB free and a 2 GiB engine allocation, and checks host ports immediately before launch. A failed bound is an actionable refusal, not permission to change host settings. Inspect actual usage with `docker stats --no-stream shipsense-local-p01-mongodb-1 shipsense-local-p01-storage-1`.

Lifecycle commands verify the local daemon, repository/state identity and ownership labels of exact project resources. They refuse a remote daemon, foreign resource, extra same-project container, remote endpoint, arbitrary database/bucket, linked state directory or credentials under the repository. No global prune, orphan removal or unrelated cleanup runs. `local:down` removes owned containers/network and **preserves all three named volumes** and external credentials. Failed startup also stops its owned profile. Other Docker resources are preserved.

Reset is deliberately explicit and destroys only the three verified synthetic volumes:

```sh
npm run local:reset -- --confirm-synthetic-reset shipsense-local-p01
npm run local:up
npm run fixtures:seed
```

Pass the same `--state-dir` when using a custom location. Reset preserves credentials. To change credentials, first reset the verified owned volumes, then archive the external state securely; initialize a fresh external path. Do not reset a database or bucket by supplying a URL. Synthetic orphan objects from interrupted seed are retained for inspection and removed only by this scoped reset; no automatic expiry deletion runs.

## Integrity and queue behavior

Six [inert manifests](../../tests/fixtures/p01) pin Astronomy Shop `product-catalog` tag 3.1.0 and its accepted revision. They have explicit scope, UTC times, freshness, expected outcome, source and payload hash. Historical or expired fixtures remain historical; never present them as current telemetry. Injected runbook text is never interpreted as an instruction or executed.

Seed validates the entire bounded batch before writing. It writes checksum-addressed, scope-specific objects using `If-None-Match: *`, verifies the stored bytes, then inserts metadata under a compound unique scope/version index. Identical retries are no-ops. Different hashes for the same scoped version fail while retaining the winner and conflicting object. Missing/corrupt existing objects fail without repairing or overwriting the referenced evidence. An object-only interrupted write can safely complete on retry. The local unique index is additive; scoped reset is its local rollback. This standalone Mongo does not validate Atlas migrations, replication or transactions.

`MemoryQueue` and its consumer live in the same worker smoke process. It accepts bounded typed synthetic envelopes, uses stable delivery IDs, rejects duplicates/reordered/expired/poison work and bounds timeout/capacity behavior. Every outcome has delivery/correlation IDs and performs zero provider effects. Restart loses messages, deduplication, sequence and attempt memory. A separately launched API and worker cannot communicate through this queue. Service Bus durability, retries, lock renewal and dead letters remain unproved.

## Checks and failure recovery

```sh
npm run test:local
npm run quality
npm run test:foundation
npm run test:web
uv build --package shipsense-local
uv build --package shipsense-api
uv build --package shipsense-worker
npm run build:web
```

Real integration tests require a running owned profile and an explicit external state directory:

```powershell
$env:SHIPSENSE_TEST_STATE = "$env:LOCALAPPDATA/ShipSense/local-p01"
npm run test:local:integration
```

On POSIX use `SHIPSENSE_TEST_STATE="$HOME/.local/state/ShipSense/local-p01" npm run test:local:integration`. The tests perform authenticated denial, concurrency, checksum/corruption, interrupted seed and actual dependency stop/restart checks. They leave bounded synthetic conflict evidence in their unique test scopes; scoped reset removes it. They stop/restart only the two owned services. Do not run concurrently with another lifecycle command. No integration test is claimed by a skipped test; SCRUM-17 supplies clean integration CI.

For a manual outage, after `local:up`, stop only one named owned service with `docker stop shipsense-local-p01-mongodb-1`. `local:check` must fail with a safe code; `local:up` restores the service and `local:check` succeeds. The same applies to storage. Port conflicts report `LOCAL_PORT_CONFLICT`; release the conflicting listener through its owner, then retry. Never stop an unknown listener automatically. A missing dependency reports safe failure without credentials or exception details.

Native async Mongo and bounded four-thread S3 adapters expose `mongo_probe()` and `objects.probe()` for the opt-in API lifespan integration. Probes return booleans within one second, including failed/over-capacity cases. S3 admission retains its slot after cancellation until underlying work actually completes; connect/read/retry bounds cap that work. Clients require explicit async shutdown. Production profiles reject these local adapters.

API liveness/version remain dependency-independent. Default readiness is safe503; explicitly set `SHIPSENSE_LOCAL_STATE_DIR` to the existing state directory to opt into [real API readiness](../../services/api/README.md). API startup only reads validated state and owns its clients/queue; it never starts or seeds services. `SHIPSENSE_TEST_STATE` with `npm run test:readiness:integration` exercises full local API dependency outage/recovery. Readiness proves access to local dependencies, not customer recovery. Local Mongo/S3/memory behavior does not establish Atlas/R2/Service Bus production parity, IAM/lifecycle, resilience, capacity or security clearance. Issuer/reference runtime, full integration CI, region/tier/residency/cost and P01 exit retain their separate gates.
