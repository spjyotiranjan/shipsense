# Infrastructure boundary

Owns local configuration and future Azure deployment definitions. From the repository root run `python scripts/validate-foundation.py` to validate `local.example.json` and the bounded synthetic fixture. Both files are credential-free and enable no effects. API and web bind to loopback using the developer commands.

The [synthetic local service runbook](local/README.md) documents the pinned Mongo/private S3 profile, explicit seed, same-process queue, ownership checks and scoped stop/reset. External credentials remain private to the OS account. Production Atlas/R2/Service Bus and Azure secret management remain separate; no paid provisioning is included.
