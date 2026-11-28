# Decision 0012 - P02 durable session storage

**Date:** 20 November 2026.
**Status:** Accepted technical design; database effects and live activation are not authorized.
**Decision owner:** Patrick Jane.

## Storage and authority boundaries

Map the existing canonical authentication records to three fixed collections in the configured database: `auth_sessions` (session digest as `_id`), `auth_accounts` (account UUID as `_id`) and `auth_session_audit` (unique per-attempt event UUID as `_id`). Use storage schema version 1, strict codecs and server validators, canonical UUID strings and bounded BSON int64 counters/times. Unique default `_id_` indexes suffice for this slice. Reject malformed, unknown-version or conflicting definitions; runtime never migrates or adopts unknown data. Store no raw handle, provider credentials, email or tenant grants. Authentication receipts remain separate from tenant-scoped audit and permissions.

No TTL, scheduled deletion, real-user retention period or live issuance is selected. Setup, application, read-only verification and explicitly approved fixture cleanup use separate minimum privileges. The application may insert audit receipts but cannot insert accounts/sessions, create collections/indexes, read or alter audit receipts, or delete records. Field-level invariants additionally depend on reviewed code and validators; collection privileges alone do not enforce them or protect against privileged administrators.

## Atomicity and failure semantics

Use explicit transactions with primary reads, snapshot read concern and majority commit. Acquire real increment fences on the session and its referenced account in that order, including revoke. All account status/epoch/revision and invalidation writers must contend on that account; reactivation advances the epoch. Concurrent insertion/deletion and missing-key races require a new accepted strategy before activation. Fixed session/account identity and timing fields are immutable; revoke uses compare-and-swap and commits its redacted receipt atomically. Repeated revoke preserves business revision and revocation time. Correlation is never an idempotency key.

Run a transaction body once. Conflicts, decode failures and compare-and-swap misses fail closed without replaying a successful authority snapshot. Only an unknown commit result permits one commit-only retry on the same transaction/event. An unresolved commit, timeout or cancellation releases no authority and makes no rollback claim; independent reconciliation must precede cleanup. Confirmed abort is distinguished from uncertain outcome. Recheck trusted time after fences and after commit, including direct authority callers; expired or cancelled requests never gain authority from later receipt discovery.

Bound the authority operation by a 2,000 ms monotonic deadline, each commit send by at most 500 ms within that budget, and cancellation cleanup by at most 250 ms additional time. Driver behavior, client/session cleanup and actual limits require proof. Do not weaken fencing or cache authority to improve contention performance. Protected operations still recheck identity and tenant grants within their own authorization/effect boundary.

## Release boundary and rationale

This design extends Decision 0011's technical direction only. Its prohibition on database writes/indexes remains until explicit scoped operator approval. Confirm nonproduction target, transaction-capable topology, actual narrow credentials and synthetic-only collection ownership before effects; stop on unknown records or incompatible capabilities. No infrastructure, spend, R2 effect, production change or default runtime/sign-in activation is implied. A durable adapter requires actual independent-process race, atomic-audit, cancellation, uncertain-commit and restart proof before acceptance. Synthetic receipts alone do not complete P02.2 or P02.5.

Rationale: make revocation/account invalidation and audit durable while refusing stale or uncertain authority; separate technical acceptance from operational permission and measured proof.

**Source:** bounded durable-session design v1, technically accepted by Patrick on 20 November 2026; prior Decisions [0002](0002-architecture-baseline.md), [0010](0010-p02-session-bridge.md) and [0011](0011-p02-canonical-session-lifecycle.md). MongoDB [transaction production considerations](https://www.mongodb.com/docs/manual/core/transactions-production-consideration/) and [PyMongo transactions](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/transactions/) inform this design; documentation does not establish deployment capability or isolation proof.
