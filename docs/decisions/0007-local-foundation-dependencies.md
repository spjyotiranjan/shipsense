# Decision 0007 — Local foundation dependencies

**Date:** 9 November 2026
**Status:** Accepted starting choices for the local P01 core; runtime compatibility and delivery acceptance remain required.
**Decision owner:** ShipSense CTO, within the accepted architecture baseline.

**Supersession:** The [integration-test acceptance amendment](#integration-tests-without-a-hosted-verification-gate--11-november-2026) removes the separate hosted-verification workflow, local/remote hosted-result and environment approval gates. The [hosted profile amendment](#hosted-profile-and-single-integration-workflow--11-november-2026) governs database naming. The [hosted-only amendment](#hosted-only-integration-supersession--11-november-2026) retires all self-hosted/container application, development and integration paths. Earlier conflicting requirements below are historical and superseded.

## Local core

Use the following exact starting dependencies with the existing pinned runtimes and single uv lock. Container references include the verified multi-platform index digest; the initial runtime target is Linux/amd64.

| Component | Selected local pin |
| --- | --- |
| MongoDB Community | `docker.io/library/mongo:8.0.34@sha256:b9924c330a8bbc5800fe9c69f04a84e221eca7b28fd049a0354147d9908fa142` |
| Private S3 development emulator | `docker.io/chrislusf/seaweedfs:4.53@sha256:ccad23e18639c8b98cee17e7100b95830a06077b56d8e5b006d6dcf8ec5e94a0` |
| MongoDB client | `pymongo==4.19.0` |
| S3 client | `boto3==1.43.126`, `botocore==1.43.126` |

MongoDB Community is SSPL licensed; PyMongo and SeaweedFS are Apache-2.0. SeaweedFS is a local development emulator, not a replacement for private Cloudflare R2. Prefer this active emulator over the archived MinIO candidate. Registry metadata and client wheel availability establish reproducible candidates, not working imports, safe configuration, absence of vulnerabilities or production parity. Resolve and freeze transitive dependencies and prove compatibility before delivery. Keep future security-update review explicit.

## Isolation and private access

Use synthetic data only, dedicated local database/bucket/volumes and an isolated Compose network. Bind MongoDB to `127.0.0.1:37017` and S3 to `127.0.0.1:38333`; publish no admin, filer or gRPC control ports. Validate target ownership before seed, stop or reset; never enumerate or remove unrelated resources. Stop preserves volumes by default. Reset requires an explicit synthetic-only target and must refuse remote or ambiguous targets.

Network isolation means a dedicated user-defined bridge with only the fixture services attached, explicit 127.0.0.1 host port bindings and a loopback bridge host-binding default. It does not require Compose internal:true and does not establish outbound network denial. Containers on this bridge can reach each other's listening ports; the Docker host remains trusted. Publish only the two specified data ports and no control ports. Prove actual bindings and host reachability, private authenticated access and denial cases on the selected runtime; configuration alone is not proof.

SeaweedFS defaults can allow anonymous access. Require a nonempty explicit identity configuration, no anonymous identity, fixture-bucket-scoped permissions and fail-closed startup validation. Disable unused services and telemetry where supported. Generate local credentials outside tracked files, fixtures, object payloads and logs; examples cannot be usable production credentials. MongoDB also requires explicit local credentials and least-privilege application access. These local controls do not establish P02 user or tenant authorization.

Acceptance requires direct authenticated access, unsigned and wrong-key denial, missing/empty-config refusal, wrong-bucket denial and secret redaction. Historical upstream security advisories remain relevant; a later version number alone is not security clearance. If the pinned build cannot enforce the required boundary, fail the slice and revisit the choice rather than relaxing isolation or privacy.

## Queue and fixtures

Use a bounded in-process queue only in the local profile, with enqueue and consumer in the same owning process for a bounded no-effect smoke command. Separate API and worker processes do not share this queue. Restart loses messages and deduplication memory. This does not demonstrate Service Bus durability, retries, lock renewal, dead letters or cross-process delivery. Reject local adapters in production profiles.

Keep envelopes and fixtures scoped by tenant, project, service, environment, provider object/version, event/observed/expiry time and correlation. Validate bounded payloads and stable delivery IDs. Demonstrate duplicate, reordered, poison and timeout cases without provider effects. Synthetic scope values are not authenticated authority.

Retain six inert fixture cases: pipeline-failure, probe-config-regression, missing-telemetry, dependency-failure, injected-runbook and deployment-regression. Pin reference provenance to Astronomy Shop `product-catalog`, demo tag `3.1.0`, revision `dedc0178918e260823323b8d95005a8cb924b007`. Store expected outcomes, provenance and checked payload hashes. Injection text remains inert. A successful deployment or gRPC health response does not establish recovered dependency health.

Write checksum-addressed objects before scoped metadata. Unchanged seed is a no-op; a same-version conflicting hash must preserve existing evidence and fail. Use a unique scoped metadata index, verify conditional writes under concurrency, and prove interrupted-seed retry without silently overwriting conflicts. Missing objects and checksum mismatch fail safely. Preserve conflicting and stale evidence.

## Runtime proof and remaining gates

Start with resource bounds appropriate to the local host: MongoDB 768 MiB with a 256 MiB cache and storage 512 MiB are initial test limits, not measured capacity guarantees. Recheck available memory and ports before startup; measure actual usage and stop only resources owned by this local profile. No host resource-setting change is implied.

Use native async PyMongo for asynchronous API access and bounded off-loop Boto3 execution with explicit connection, read, retry and concurrency limits. Bound readiness probes and clean up clients at shutdown. Prove positive access, outage/recovery, concurrency limits, liveness independence, frozen installs and affected builds/contracts. Do not expose credentials, dependency addresses or exception details in public diagnostics.

Issuer selection and runtime acceptance remain unresolved. Dex 2.46.1 is an evaluation candidate with conflicting advisory metadata; source guards alone do not clear it. Its restricted grants, discovery/JWKS, key rotation and host/container reachability need separate validation. Reference runtime and its PostgreSQL/flagd/collector dependencies remain unaccepted candidates; the core fixture provenance does not require starting that topology. Full P01 exit retains issuer/reference validation, clean integration CI and region/tier/residency/cost review.

Production remains MongoDB Atlas on Azure, private Cloudflare R2 and Azure Service Bus under Decision 0002. Local standalone MongoDB, S3 emulation and memory queues do not prove production replication, recovery, IAM, lifecycle or capacity. No region, SKU, AI model, retention value or paid resource is selected here. Actual recurring spending still requires owner approval.

## Rationale and sources

Keep the core development loop reproducible and cloud-credential-free while explicitly testing private access, evidence integrity and emulator limits. Independent issuer/reference validation can follow without blocking the bounded core.

- [Architecture baseline](0002-architecture-baseline.md) and [P01 backend plan](../backend-implementation/p01-repository-and-developer-foundation.md).
- [PyMongo 4.19.0 support](https://github.com/mongodb/mongo-python-driver/blob/4.19.0/README.md), [MongoDB lifecycle](https://www.mongodb.com/legal/support-policy/lifecycles) and [security alerts](https://www.mongodb.com/alerts).
- [SeaweedFS 4.53](https://github.com/seaweedfs/seaweedfs/releases/tag/4.53), [authentication defaults](https://github.com/seaweedfs/seaweedfs/blob/4.53/weed/s3api/auth_credentials.go) and [security advisories](https://github.com/seaweedfs/seaweedfs/security/advisories).
- [R2 Boto3 compatibility](https://developers.cloudflare.com/r2/examples/aws/boto3/).
- [Pinned reference service](https://github.com/open-telemetry/opentelemetry-demo/blob/dedc0178918e260823323b8d95005a8cb924b007/src/product-catalog/main.go).
- [Dex advisory](https://github.com/dexidp/dex/security/advisories/GHSA-7qjx-gp9h-65qj) and [candidate grant guards](https://github.com/dexidp/dex/blob/v2.46.1/server/grants/grants.go).

## CI smoke isolation and browser automation — 9 November 2026

**Status:** Accepted starting design; implementation, runtime compatibility and independent delivery acceptance remain required.

Keep the default synthetic namespace shipsense-local-p01 and allow exactly one additional opt-in namespace shipsense-ci-p01 for clean integration smoke. Retain the selected images/clients, local-only profile, fixed loopback ports 37017/38333, database/bucket names, memory limits and privacy safeguards. These namespaces cannot run concurrently on one host. Reject arbitrary project names, endpoints, ports, remote daemons and production profiles.

Each CI smoke attempt creates fresh credentials and a new private external state directory with its own owner identity. Bind lifecycle operations to the explicit namespace, repository, state identity and exact resource names/Compose labels. Reject mismatched state, inherited namespace overrides, unknown or stale resources and occupied ports before effects. Never adopt another attempt's resources or reuse existing local credentials/volumes. Preserve all shipsense-local-p01 volumes and private state. Failure and cancellation cleanup may remove only verified resources owned by the current CI attempt, including its CI volumes after explicit synthetic reset validation; ambiguity causes refusal. Delete only the attempt's validated external disposable state after its resources are safely handled. No prune, orphan sweep, automatic listener termination or host configuration change.

Use the pinned Node runtime's built-in WebSocket/CDP capabilities against an already installed Chrome/Chromium for the real built-web diagnostic smoke. No added browser library, browser download, extension or authenticated user profile is selected. Detect and record the actual executable/version and prove compatibility on each environment; absence or protocol failure fails the required gate. Launch an owned headless browser with a unique private external user-data directory and loopback-only debugging endpoint. Restrict navigation and debugging connections to validated test-owned loopback targets, use bounded commands/timeouts and stop only owned processes. Never attach to an existing browser/debugging service or use real cookies/provider secrets. Keep sanitized captures/logs outside the product tree with bounded CI artifact retention; exclude credentials and browser-profile data.

Rationale: clean CI must prove independent boot without consuming or resetting preserved developer state; real UI failure/recovery should use the existing runtime without another package dependency. These choices do not select issuer/reference runtimes, establish production parity or authorize cloud spending.

Sources: Decision 0007 local privacy/lifecycle baseline and P01.5 clean integration acceptance; https://docs.docker.com/compose/how-tos/project-name/ ; https://developer.chrome.com/blog/remote-debugging-port .

## Private Mongo bootstrap compatibility — 10 November 2026

**Status:** Accepted local development/CI design; runtime compatibility and independent delivery acceptance remain required.

Keep external host credential files owner-only and their directory private. Do not relax host permissions to accommodate the container UID. A bounded root bootstrap wrapper may copy only the two declared Mongo bootstrap credential inputs from read-only bind mounts into a dedicated container tmpfs capped at 1 MiB. Set its directory to 0700 and copied files to 0600, owned by the image's mongodb account on every start. Fail closed on missing, unreadable or invalid inputs or unavailable tmpfs. Then exec the unchanged pinned official entrypoint, preserving its privilege drop and command/signal behavior. Do not inject credential values through Compose environment, command arguments or logs; the upstream entrypoint's internal file processing is not a new credential transport. Never copy these inputs into image layers, writable container layers, persistent volumes or artifacts. Tmpfs is removed when the container stops, but host swap may persist its contents; no swap-proof secrecy is claimed and no host setting change is authorized. Retain image/client pins, memory limits, namespaces, loopback bindings, private-access checks and owned-resource cleanup. This is local compatibility, not production identity or security clearance.

Rationale: Linux owner-only bind files must remain private while Mongo's bootstrap runs after its upstream privilege drop.

Sources: https://raw.githubusercontent.com/docker-library/mongo/master/8.0/docker-entrypoint.sh ; https://docs.docker.com/engine/storage/tmpfs/ .

## Hosted MongoDB and Cloudflare R2 application setup — 10 November 2026

**Status:** Accepted; supersedes the local MongoDB/S3 application-default and developer-provisioning scope above. Earlier local implementation and verification remain historical evidence, not proof of hosted operation.
**Decision owner:** ShipSense project owner; isolated CI-fixture boundary accepted by the CTO.

Application configuration uses existing hosted MongoDB and private Cloudflare R2 endpoints and access. Do not start or require self-hosted MongoDB or S3 emulators for application/developer setup. Keep connection settings and credentials server-only; commit only nonfunctional placeholders in env.example. Missing, placeholder or invalid configuration must fail closed: credential-free liveness/version and web diagnostics remain available while readiness is 503. Validate configuration before creating clients; retain bounded connection/read/retry/concurrency limits, cancellation and clean shutdown. Do not expose endpoint addresses, credentials or underlying exception details in public responses, browser bundles, logs or artifacts. Preserve TLS certificate verification for hosted connections and private bucket access. Configuration support does not itself authorize provider calls, schema changes, seed writes or production effects.

Explicitly isolated synthetic containers may remain solely as credential-free automated test fixtures, never the application's default, developer provisioning path or implicit fallback when hosted configuration fails. Retain the existing pinned test images, exact namespace/ownership checks, private access, resource bounds, attempt-specific credentials and cleanup safeguards. Test-only transport exceptions must be isolated from hosted configuration and must not permit arbitrary remote endpoints or disable hosted TLS verification. Existing developer volumes and private state must be preserved; this decision does not authorize their deletion. Tests must exercise the hosted client/configuration boundary and safe failure behavior; emulator success cannot establish Cloudflare R2 or managed MongoDB compatibility, permissions, residency or live readiness.

Apply this setup change across affected application, examples, runbooks, technical plans and CI. Keep historical local proof identified by profile and revision, and disclose that live hosted verification remains unperformed until configured endpoints and authorized access are available. No paid provisioning, recurring-spend approval, production permission, region/tier selection or full P01 exit is inferred. Queue, issuer/reference, integrity, scope/audit and production-governance requirements otherwise remain unchanged.

Rationale: the owner will use hosted MongoDB and Cloudflare R2 access and does not want manual self-hosting now. Synthetic test fixtures retain reproducible credential-free failure checks without becoming application infrastructure.

Sources: authenticated owner comments 3d27374b-a2e4-4acd-a2a7-5ddfaee68288 and 83b7ed01-1827-43c8-a7d8-e0163b5dbeae (10 November 2026); Decisions 0002 and 0007 privacy, integrity and lifecycle constraints.

## Private synthetic S3 bootstrap compatibility — 10 November 2026

**Status:** Accepted automated-test-fixture design; pinned-image runtime proof and independent delivery acceptance remain required. This does not change hosted MongoDB/private Cloudflare R2 application setup.

Keep the single declared synthetic S3 identity configuration s3.json on an owner-only host file in a private external state directory, mounted read-only. Do not relax host permissions for a container UID. A bounded root wrapper may stage only this validated configuration into a dedicated container tmpfs capped at 1 MiB. Before copying, refuse missing, unreadable, empty, oversized or invalid input, a missing image seaweed account, unavailable tmpfs or an unexpected staging path. Retain existing scoped-identity/no-anonymous/bucket validation; do not expand fixture privileges. Validate actual tmpfs backing rather than silently using the writable container layer. Set the staging directory to 0700 and copied file to 0600, owned by the pinned image's seaweed account on every start. Route the S3 configuration file-path argument to that staged file and exec the unchanged pinned /entrypoint.sh, preserving upstream privilege drop, command and signal behavior. Credential values must not enter arguments, environment, image layers, writable layers, persistent volumes, logs or artifacts. Do not print configuration content on failure. Tmpfs lifecycle does not establish swap-proof secrecy; host swap may persist contents, and no host setting change is authorized.

Retain image/client pins, memory limits, fixed loopback ports, exact fixture namespace/state/resource ownership, private access and cleanup safeguards. Preserve existing developer volumes and private state. This compatibility extension applies solely to isolated automated synthetic fixtures, never application/developer provisioning or fallback. It authorizes no provider calls, hosted writes, new images/dependencies, production effects or spending.

Rationale: the selected storage entrypoint drops to seaweed before the service reads private identity configuration, so owner-only bind files need narrowly scoped ephemeral staging without weakening host privacy. Retrieved tag source supports the design; runtime evidence must independently establish the actual pinned image's entrypoint, account, tmpfs, permissions and process behavior.

Sources: https://raw.githubusercontent.com/seaweedfs/seaweedfs/4.53/docker/entrypoint.sh ; https://docs.docker.com/engine/storage/tmpfs/ ; Decision 0007 hosted-setup and private bootstrap constraints.

### Digest validation clarification — 10 November 2026

For the isolated synthetic S3 fixture, the trusted host lifecycle must first validate the complete private scoped identity configuration against the attempt settings using its existing semantic validation. It may supply only the SHA256 of those exact validated configuration bytes to the root wrapper as an expected-integrity value. This digest is not an authorization credential and must not replace semantic validation, private input handling, attempt ownership or scoped-access checks. Do not derive it blindly from an unvalidated mounted file. Keep both configuration values and digest out of logs and published artifacts.

Before staging, require a correctly formed expected digest, a readable nonempty size-bounded declared input and an exact digest match. After staging only that file into the verified dedicated tmpfs with seaweed-owned directory0700/file0600, verify the copied bytes match before exec of the unchanged pinned entrypoint. Missing/malformed digest, changed/empty/oversized/unreadable input or unavailable tmpfs must refuse service startup without printing input. No jq or new package/image is required by this design; actual pinned tools and behavior remain verification gates. Host files remain private/read-only, service privilege drop remains intact, and hosted application setup and all prior isolation/cleanup boundaries remain unchanged.

## Hosted-only integration supersession — 11 November 2026

**Status:** Accepted owner direction; supersedes every earlier permission in this record to use Docker, self-hosted MongoDB/S3, or synthetic container fixtures in the active application, development or integration path. Historical implementation and proof remain historical; they do not establish current hosted compatibility.
**Decision owner:** ShipSense project owner. Technical verification boundaries are accepted by the CTO within the architecture baseline.

Use existing hosted MongoDB and private Cloudflare R2 for both application configuration and integration verification. Remove the active Compose/container lifecycle, image bootstrap and container smoke path, including implicit test fallback. Keep SDK privacy/boundedness, configuration and no-effect queue tests without starting hosted substitutes. Preserve existing developer volumes/private state; removing support is not authorization to delete those resources. This change does not select a replacement identity/reference runtime.

Provide one documented bounded read-only hosted integration command using the server-only settings named in env.example. Use a dedicated non-production database identity and private R2 bucket-scoped read-only credentials supplied privately in an ignored local .env or a protected GitHub environment. Never reuse MCP/account-management tokens as database/S3 application credentials. Validate TLS and configuration before clients, keep endpoint/credential details out of public responses and logs, and close all clients on success, failure, timeout and cancellation. No enumeration of unrelated databases/buckets or retrieval of customer object contents is required. Use only the minimum configured-target metadata/read operations needed to establish reachability and authority. Anonymous/wrong-key and bounded failure tests must not alter valid hosted state or stop remote services.

Untrusted PR checks perform frozen installs, quality/contracts, unit tests and builds with no hosted secrets. Hosted integration is a separate explicitly invoked manual workflow on reviewed code, using a protected environment and narrow non-production credentials. Do not execute unreviewed PR code with environment secrets. Missing or invalid settings fail the hosted command/workflow explicitly; do not convert missing access into a skipped passing live result. Local and remote hosted success are separate evidenced delivery gates. No provisioning, schema/index/seed/object writes, production effects or recurring spending is authorized.

Update P01.3 acceptance to documented hosted setup, private server configuration, safe unconfigured diagnostics and bounded read-only compatibility proof; remove its former new-developer seeded-container requirement from active criteria. Preserve prior local acceptance by revision as historical proof. Update P01.5 acceptance to clean credential-free build/contract/unit CI plus the same documented hosted integration command run locally and in its protected manual workflow. Keep observable safe configuration failure, client cleanup and web-to-API success/failure/recovery checks; induce local test-owned failures rather than disrupting hosted services. Refresh both existing phase technical plans, runbooks, examples, workflow, roadmap and status references consistently. Full P01 exit remains open until actual hosted access and all other required criteria pass.

Rationale: the owner uses hosted endpoints and explicitly requested removing Docker/self-hosting from integration to simplify the development path.

Sources: authenticated user comments 6c7b8ffa-afbb-47d4-8a84-43d4ffb5d5a8 and a1675686-0d8d-4c76-bae2-e507b496fe2f (10 November 2026 UTC; 11 November Asia/Kolkata). Architecture Decision 0002 and this record's hosted privacy, boundedness and no-effect constraints otherwise remain in force.

## Hosted profile and single Integration workflow ? 11 November 2026

**Status:** Accepted; supersedes dependency selectors and the separate hosted workflow above.

MongoDB configuration supplies a validated base database name and server profile. Derive the effective database exactly as `{base}-{profile}`; validate the final database name before client creation. Retain the foundation's local-only profile and production refusal until production authority is implemented. Hosted MongoDB and private Cloudflare R2 are the sole dependency path. Remove the dependency selector and obsolete alternatives.

Use one workflow named Integration. Its pull-request/push diagnostics remain credential-free. An explicitly manual job on reviewed code uses the protected environment's dedicated non-production read-only settings; provider secrets never enter untrusted PR jobs. Keep TLS verification, redaction, deadlines, cancellation, client cleanup, no provider writes and no spending authorization. Local and protected remote hosted outcomes remain separate evidence gates.

Keep supplied ignored local configuration private. Commit only placeholder values in `.env.example`; the example is never a credential source. Update existing phase criteria, plans and runbooks consistently.

Source: authenticated owner comment `c506f5bd-9608-4721-ba0c-5f83a23c57f8`; dated canonical transcription delegated in Patrick handoff `2ef95baf-af1a-47ff-8d16-b0dc9f87ef3d`.

## Integration tests without a hosted-verification gate — 11 November 2026

**Status:** Accepted project-owner direction. Supersedes this record's mandatory local/protected remote hosted-verification outcomes, protected hosted-run approval gate and manual hosted workflow requirement. Other hosted application configuration and safety constraints remain.

Retain meaningful integration tests and credential-free build/contract/unit/API/web/browser failure-recovery checks. Where existing integration tests support real MongoDB and private R2 connections, use privately supplied hosted environment settings in those integration tests only. Otherwise leave unsupported coverage explicit; do not build a new hosted-verification system or reintroduce Docker/self-hosted fixtures. A separate hosted-verification run, protected remote hosted result or environment approval is not required for P01.3/P01.5 acceptance. Remove the obsolete manual hosted-verification job and related release-gate instructions. Preserve actual historical local hosted results as evidence without claiming an unperformed remote result or converting skipped tests into passes.

Keep the application's server-only hosted MongoDB/R2 configuration, validated `{base}-{profile}` database naming, placeholder-only example and safe unconfigured readiness. Test-only connection settings must remain private and isolated from credential-free/untrusted PR execution. Retain TLS verification, configured database/bucket scope, redaction, deadlines, cancellation and client shutdown. No provider writes, provisioning, production effects, service disruption or spending authority is granted. Apply the revised test/acceptance boundary consistently in P01 criteria, existing plans, runbooks, workflow and status; all other required local checks, independent exact-current-SHA review and acceptance remain.

Rationale: the owner requests integration tests without a separate hosted-verification release process.

Source: authenticated PAT-104 user comment `af027d52-c4e4-44dc-af9a-3a11ebaddf0f`, 11 November 2026.
