# Infrastructure boundary

Application development and integration use existing hosted MongoDB and private Cloudflare R2. Configure server-only values through [.env.example](../.env.example) and the [developer guide](../docs/developer-setup.md). This repository does not install or operate database/storage services.

Azure deployment, Key Vault/managed identity, Service Bus and paid provisioning remain governed by the accepted architecture and measured phase gates. Hosted integration is read-only and never provisions, seeds, resets or restarts provider services.
