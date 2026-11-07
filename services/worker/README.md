# Worker boundary

Owns future asynchronous ingestion/investigation/verification jobs. Current entrypoint executes one local diagnostic, emits `processed: 0` and `effects: 0`, and exits. It has no queue, provider client, data store or effect capability.

From the root: `uv build --package shipsense-worker`; `uv run --frozen --package shipsense-worker shipsense-worker`. `SHIPSENSE_PROFILE` defaults to `local`; an unsupported profile produces `LOCAL_PROFILE_REQUIRED` and exits 2 without echoing input. P01.3 adds the local adapter; production work requires the governed action and permission framework later.
