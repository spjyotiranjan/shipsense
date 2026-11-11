# Worker boundary

Owns future asynchronous ingestion/investigation/verification jobs. The default entrypoint executes one local diagnostic, emits `processed: 0` and `effects: 0`, and exits. `npm run queue:smoke` enqueues and consumes bounded inert envelopes in this same process, proving duplicate/reordered/poison/timeout outcomes with zero effects. Restart loses messages and all queue memory; a separate API process does not share it.

From the root: `uv build --package shipsense-worker`; `uv run --frozen --package shipsense-worker shipsense-worker`. `SHIPSENSE_PROFILE` defaults to `local`; an unsupported profile produces `LOCAL_PROFILE_REQUIRED` and exits 2 without echoing input. See the [local runbook](../../infra/local/README.md) for shared adapters and tests. Production work requires the governed action and permission framework later.
