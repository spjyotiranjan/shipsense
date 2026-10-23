# Decision 0002 — Architecture baseline

**Date:** 23 October 2026
**Status:** Accepted as an implementation baseline; SKU, issuer, model, lifecycle values and spending are selected at measured phase gates.
**Decision owner:** ShipSense project owner.

## Boundaries

Next.js/TypeScript owns presentation and the backend-for-frontend layer: sessions, UI composition, and calls to the main API. Python FastAPI owns canonical APIs, authorization, policy, integrations, and action orchestration. Ingestion, investigation, verification and replay run in workers/jobs. FastAPI publishes versioned OpenAPI and Swagger UI. Browsers and AI tools never receive provider credentials.

| Area | Chosen baseline and alternative | Reason and validation |
| --- | --- | --- |
| Hosting | Azure Container Apps for Next.js, FastAPI and workers; Container Apps Jobs for finite replay/verification. Compare a Vercel-hosted Next.js front end and Azure App Service in P01/P06 if measured behavior or cost favors them. | Separate workload scaling without operating ShipSense Kubernetes. Verify streaming, cold starts, network behavior, isolation and cost. |
| Async events | Azure Service Bus queues/topics and idempotent workers; in-process work only for local development. | Durable retries and dead letters; test duplicate, reordered, poison and delayed events. |
| Database | MongoDB Atlas on Azure, colocated with the app where available; tenant-scoped indexes and time-aware event/projection records. Self-hosting needs a new decision. | Validate Central India tier, backup/restore, connectivity, latency and price. Application records alone are not an immutable audit archive. |
| Objects | Private Cloudflare R2 buckets for bounded snapshots, attachments, exports and replay. Azure Blob was considered, but R2 is the owner's choice. | Store checksum, classification and expiry in MongoDB. Define lifecycle expiry before ingestion; test encryption, presigned access, deletion and egress. |
| Secrets/health | Azure Key Vault, managed identity where available, Application Insights/Log Analytics for ShipSense health; source-linked OpenTelemetry for customer evidence. | Test rotation/revocation, redaction, alerts, and telemetry loss. |
| AI | LangGraph for resumable workflows and human pauses; LangChain adapters where useful; OpenAI API behind a versioned adapter. | Tenant-isolate MongoDB checkpoints; P12 selects model/version by quality, latency, cost and data handling. Deterministic policy and human approval govern effects. |
| API | FastAPI OpenAPI is canonical; Next.js uses generated or schema-validated typed client. | CI checks compatibility and prevents a second domain API. |
| Identity | OIDC for Release 1 with a local development issuer; enterprise SAML/SCIM later. | Validate effective permissions at API, workers, tools and callbacks. |
| Connectors | GitHub, Actions, Jira, Azure deployments and Vercel deployments in Release 1 behind capability-labeled adapters. | Preserve raw IDs, source links, authority, event time and receipts; hide unsupported effects. |

## Security and data decisions

Use separate narrow provider credentials per tenant. Keep them in Key Vault, rotate and revoke on disconnect, and never copy them into prompts, browser state or R2. Every effect rechecks ShipSense policy and provider authority. Record AI recommendation, deterministic policy result, human approval, provider receipt and observed outcome separately. Material artifact/config/policy changes invalidate approval. Freeze model/prompt/tool/policy versions for replay. Test cross-tenant denial in MongoDB queries, R2 keys, graph checkpoints, logs and prompts.

P03 defines R2 retention classes and deletion tests before live data ingestion. Initial fixtures use short-lived raw evidence and retain sanitized replay only as needed for evaluation; exact day counts depend on classification and pilot requirements. No indefinite retention is implied.

## Cost and deployment check

Start with the smallest reliable configuration for 20–30 active users, not a free tier that invalidates recovery or access testing. P01 records an itemized forecast, quotas, alert thresholds and teardown steps before paid provisioning. Central India is provisional pending service/Atlas availability and pilot residency checks. Vercel is a Release 1 customer deployment connector and an optional Next.js hosting comparison; it is not the FastAPI backend.
