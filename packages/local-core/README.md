# Shared dependency utilities

The `shipsense-local` package name is retained for workspace compatibility. It contains bounded verified-TLS private object access, safe error codes, inert fixture validation and the same-process no-effect queue. It has no service lifecycle, database hosting, seed/reset commands or container dependencies.

The API supplies hosted MongoDB/R2 settings; see [API configuration](../../services/api/README.md). Unit tests cover fixture checksum/scope/path validation, queue duplicate/reorder/expiry/timeout behavior, storage deadlines, retained capacity after cancellation and draining shutdown. Inert manifests are never uploaded by diagnostics or integration checks.
