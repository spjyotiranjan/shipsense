# Infrastructure boundary

Application/developer setup uses existing hosted MongoDB and private Cloudflare R2 endpoints through root [env.example](../env.example) and the [API runbook](../services/api/README.md). No self-hosted database/storage or paid provisioning is part of setup. Connection secrets stay server-only; production uses Azure secret management when deployment gates are implemented.

[Isolated automated fixtures](local/README.md) retain pinned synthetic Mongo/private S3 solely for credential-free integration tests. They are never an application fallback. `python scripts/validate-foundation.py` checks the inert `local.example.json` and foundation fixture; that historical fixture configuration enables no effects and is not hosted connection configuration. API/web bind to loopback. Azure deployment, issuer/reference and region/tier/residency/cost remain separate gates.
