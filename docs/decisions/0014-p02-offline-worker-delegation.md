# Decision 0014 — P02 offline worker delegation boundary

**Date:** 28 November 2026.
**Status:** Bounded implementation choice for credential-free proof; no runtime integration.

Build a no-effect worker harness for one fixed metadata-count capability. Keep worker credential verification behind an internal port with a fixed, separate audience; the harness does not choose a token format, enable an issuer or grant provider authority. A successful verification provides the worker identity, trusted tenant and deadline. A queue envelope supplies only the requested job/delegation identifiers and exact scope. The trusted directory locates a current grant by that tenant and both identifiers; the harness compares the returned identifiers, worker, scope and lifetime before acquiring current principal authority through the same audited read gateway as tool counts. Reload on every invocation; neither a previous result nor a queue payload can establish authority. Denials at this boundary have one shape. Invalid credentials and unavailable directory dependencies are not proof of a recorded tenant decision.

The harness supports no queue producer, effect, connector callback, token issuance, or persistent claim/replay operation. Actual workload credentials, connector-specific verification, durable delegation revocation races and provider authority remain gated. See the [backend plan](../backend-implementation/p02-identity-tenancy-permissions-and-audit.md#p023-authorization-and-untrusted-work).

The no-effect metadata and audit query gateways check the observed grant and effective principal deadlines both after the audit append and before releasing results. They compare instants in UTC, including when the local clock repeats an hour. A recorded allowed admission is not proof that data was fetched or released. These checks are not an authority fence or a substitute for handling concurrent revocation in a persistent adapter.
