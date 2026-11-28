# Decision 0015 - P02 audit collection identity and commit budget

**Date:** 28 November 2026.
**Status:** Proposed. Runtime activation remains gated by Decision 0012.

## Audit append

Evaluate MongoDB 8.0 `bulkWrite` with one insert and a configured expected BSON collection UUID in `nsInfo`. Resolve that UUID against validated collection metadata at setup. Use the authorized application session and require definitive success for the one write. A missing or replaced namespace must abort the transaction. Keep application privileges insert-only on the audit collection. Validator changes that preserve the same UUID still require separate setup verification and controlled DDL.

A disposable, network-isolated MongoDB 8.0.34 replica set accepted this command with an insert-only audit role. The server returned `CollectionUUIDMismatch` (361) after the collection was moved and again after a replacement was created. The probe observed zero writes to the replacement and confirmed that the missing collection was not implicitly created. Adapter integration and concurrent DDL proof remain open.

## Commit budget

Do not use PyMongo client-side operation timeout as the sole commit budget. The pinned 4.19.0 driver sent three commits for one transaction after two dropped acknowledgements with `timeoutMS` set and `retryWrites=False`. [The loopback regression](../../services/api/tests/test_pymongo_commit_wire.py) records the actual sends and verifies that the transaction body ran once. With client-side operation timeout disabled, the same two lost acknowledgements produced exactly two sends and an unknown commit result.

Evaluate whether a dedicated client without client-side operation timeout, an externally bounded commit call, and explicit socket/server limits satisfy Decision 0012. Verify the retry classification, overload handling, send count, and 500 ms per-send, 2 s operation, and 250 ms cleanup limits under faults. An accepted implementation must retain the existing unknown-outcome and reconciliation semantics. This proposal makes no change to those limits.

**Source:** [MongoDB 8.0 bulkWrite command](https://www.mongodb.com/docs/v8.0/reference/command/bulkwrite/) and [Decision 0012](0012-p02-durable-session-storage.md).
