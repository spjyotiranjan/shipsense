# Infrastructure boundary

Owns local configuration and future Azure deployment definitions. From the repository root run `python scripts/validate-foundation.py` to validate `local.example.json` and the bounded synthetic fixture. Both files are credential-free and enable no effects. API and web bind to loopback using the developer commands.

P01.3 selects and verifies MongoDB, queue and private R2-compatible development services. No emulator, cloud runtime, paid resource or deployment command is selected here. Azure secrets later use Key Vault and managed identity. No reset/delete command exists in this slice.
