# ShipSense project roadmap

**Planning baseline:** 23 October 2026. **Project state:** P00 complete; product implementation has not started. This plan covers the full portfolio vision in the product specification and the stack chosen by the project owner. Phase numbers express dependencies, not calendar promises.

## Product outcome

ShipSense is a project centered CI/CD and operations control plane. It connects existing source control, CI, deployments, telemetry, alerts, and Jira. Its signature journey is **failure or alert → scoped evidence → competing hypotheses → governed proposal → verified draft PR → observed health → replay case**. Every claim, action, approval, and result must retain source, time, scope, and audit context.

The authoritative product source is `docs/shipsense-full-product-specification.pdf`. Its proposed implementation instructions are background requirements; this roadmap and future recorded decisions determine actual execution.

## Fixed stack and proposed deployment baseline

| Concern | Decision |
| --- | --- |
| Web | Next.js with TypeScript; server side web layer calls the main API |
| Main API | Python FastAPI with generated OpenAPI/Swagger UI |
| Data | MongoDB for tenant data, projections, workflows, and evidence metadata |
| Object storage | Cloudflare R2 for bounded evidence snapshots, attachments, exports, and replay fixtures |
| AI | LangChain, LangGraph, OpenAI API; tool access passes through ShipSense authorization and policy |
| Work tracking | Jira for project delivery; Jira also becomes a customer integration. Create each phase epic and sprint only when that phase starts; put every subphase of that phase in its sprint. See `docs/JIRA_WORKFLOW.md`. |
| Hosting | Azure Container Apps for web/API/workers, Container Apps Jobs for bounded jobs, Service Bus for asynchronous work, Key Vault for secrets, Application Insights/Log Analytics for operations; Vercel is also a Release 1 deployment connector and optional web hosting comparison |

The architecture baseline and release scope are recorded in `docs/decisions/0001-release-1-scope.md` and `0002-architecture-baseline.md`. Central India is a provisional first region; P01 validates service availability, Atlas tier, residency, latency, and cost before paid provisioning. Keep R2 objects private and expose short lived scoped access. Keep provider execution in the provider, with ShipSense owning context, policy, and audit.

## Status system

`Not started` means no accepted evidence. `In progress` means work has begun. `Blocked` records the unmet prerequisite. `In review` means implementation exists but exit proof is pending. `Complete` requires every required subphase and exit criterion to pass. `Deferred` requires an explicit scope decision. Record status changes and evidence in `PROJECT_STATUS.md`; do not equate Jira ticket closure with proof.

## Release boundaries

| Release | Product promise | Phase gate |
| --- | --- | --- |
| Foundation demo | A signed in user can trace a GitHub change through Actions and Jira to Azure or Vercel deployment evidence and health | P00–P07 |
| Release 1: trustworthy loop | An operator can investigate failed runs or alerts across GitHub, Actions, Jira, Azure and Vercel; challenge evidence, create a verified draft PR under approval, and replay the outcome | P08–P13 |
| Release 2: delivery breadth | Jenkins, Kubernetes/Argo, Netlify, Railway, Render, release/security workflows, and more complete manual controls use the shared action contract | P14–P16 |
| Release 3: enterprise operation | Organization governance, lifecycle, recovery, analytics, and enterprise connectivity are operationally credible | P17–P19 |

Release 1 includes GitHub, GitHub Actions, Jira, Azure deployments, Vercel deployments, and bounded OpenTelemetry/health evidence. Jenkins, Kubernetes/Argo, Netlify, Railway, and Render have later milestones. The owner chose this breadth to demonstrate the DevOps journey; see Decision 0001.

## Phases and subphases

Detailed plans, expected results, and acceptance criteria for every phase and subphase are indexed in [`Phases/README.md`](Phases/README.md). `PROJECT_STATUS.md` remains the current status source.

### P00 — Scope and technical decisions · Complete
**Prerequisite:** product PDF and owner's stack choices. **Exit:** accepted decision records, active-phase Jira backlog, and an agreed Release 1 reference scenario.

- [x] P00.1 Read the product specification, including trust rules, acceptance journeys, and release contradictions.
- [x] P00.2 Record the owner's Next.js, FastAPI, MongoDB, R2, LangChain/LangGraph, OpenAI API, Swagger, Jira, and Azure choices.
- [x] P00.3 Write this roadmap, status method, and repository handoff.
- [x] P00.4 Decide Release 1 integration order, demo service, identity model, provisional region, spending controls, and measurable exit thresholds.
- [x] P00.5 Record the architecture baseline for Azure services, MongoDB hosting, queue/worker model, R2 retention, provider credentials, and model selection method.
- [x] P00.6 Configure the Jira phase workflow in The Mentalists; create only P00 epic SCRUM-6 and unstarted sprint 35, containing all six subphase issues. Dates, team assignments, estimates, and sprint start are manual.

### P01 — Repository and developer foundation · Not started
**Prerequisite:** P00 architecture decisions. **Exit:** reproducible local boot, automated checks, and a working web-to-API request.

- [ ] P01.1 Establish `apps/web`, `services/api`, `services/worker`, `packages/contracts`, `infra`, `docs`, and test fixtures.
- [ ] P01.2 Pin language/tool versions, lockfiles, formatting, linting, typing, secret scanning, and branch checks.
- [ ] P01.3 Add local MongoDB, queue emulator/adapter, R2 compatible development storage, and seeded demo data.
- [ ] P01.4 Build Next.js shell and FastAPI health/version endpoints; document Swagger/OpenAPI contracts.
- [ ] P01.5 Create CI that builds both apps and runs contract, unit, and smoke checks.

### P02 — Identity, tenancy, permissions, and audit · Not started
**Prerequisite:** P01. **Exit:** denied access never exposes another tenant; all material decisions have correlated audit records.

- [ ] P02.1 Define organizations, projects, teams, services, environments, users, roles, and service accounts.
- [ ] P02.2 Implement login/session and token validation across web, API, workers, and provider callbacks.
- [ ] P02.3 Enforce tenant/resource/environment permissions at every API and tool call; test negative cases.
- [ ] P02.4 Add policy decisions, separation of duties, expiring approvals, and step-up for sensitive actions.
- [ ] P02.5 Record immutable-at-application-level audit events; plan tamper evidence and export.

### P03 — Data, events, and evidence foundation · Not started
**Prerequisite:** P02. **Exit:** duplicate or reordered events yield the same current state and preserved history.

- [ ] P03.1 Define canonical IDs and state machines for service, run, artifact, release, incident, investigation, proposal, and outcome.
- [ ] P03.2 Design MongoDB collections, indexes, retention, tenant boundaries, and schema migration rules.
- [ ] P03.3 Implement signed webhook ingestion, polling/backfill, idempotency, retries, dead letters, and reconciliation.
- [ ] P03.4 Store evidence metadata in MongoDB and bounded binary snapshots in private R2 with checksums and expiry.
- [ ] P03.5 Build provenance and freshness fields: provider object, version, valid/observed time, access result, and source link.

### P04 — Catalog and shared web experience · Not started
**Prerequisite:** P03. **Exit:** a user can find a service, see its owner and connections, and understand partial coverage.

- [ ] P04.1 Implement service discovery, ownership, repository/environment mapping, and ambiguity review.
- [ ] P04.2 Build fleet, catalog, Service 360, shared scope bar, search, timeline, and evidence drawer.
- [ ] P04.3 Add loading, empty, stale, denied, disconnected, rate limited, and historical states.
- [ ] P04.4 Add accessible keyboard journeys and alternate table views for graphs.
- [ ] P04.5 Preserve exact object/time/environment scope in deep links and exports.

### P05 — GitHub, Actions, and Jira reference integration · Not started
**Prerequisite:** P03–P04. **Exit:** failed PR run is traceable to exact attempt, job, log, artifact, Jira work item, and affected service.

- [ ] P05.1 Connect GitHub App with least privilege, webhook verification, installation mapping, and revocation.
- [ ] P05.2 Normalize commits, PRs, checks, Actions workflow runs, jobs, attempts, tests, and artifacts.
- [ ] P05.3 Render pipeline DAG, logs, test failure clusters, retry history, and superseded commits.
- [ ] P05.4 Offer authorized manual retry/cancel controls with provider receipt, idempotency, and policy.
- [ ] P05.5 Prove source-to-run-to-artifact lineage with a deliberate failing fixture.
- [ ] P05.6 Connect Jira issue/project identity, permission-scoped backfill/webhooks, links to PR/check/run, and governed issue updates.

### P06 — Azure and Vercel deployments with observability · Not started
**Prerequisite:** P03–P05. **Exit:** service view links exact Azure/Vercel deployed revision, deployment state, runtime fault, and SLO signal.

- [ ] P06.1 Connect Azure deployment state, revision/config metadata, logs, health, historical relationships, and capability-scoped manual controls.
- [ ] P06.2 Connect Vercel deployment/project/environment state, revisions, logs, health, and supported manual controls.
- [ ] P06.3 Connect bounded OpenTelemetry and source-linked metrics/traces; support Grafana where reference telemetry uses it.
- [ ] P06.4 Define SLIs/SLOs, error-budget views, burn alerts, and release overlays.
- [ ] P06.5 Demonstrate probe/config failure, deployment regression on Azure and Vercel, and explicit missing telemetry.

### P07 — Connectors and control-plane continuity · Not started
**Prerequisite:** P05–P06. **Exit:** a disconnected provider makes affected surfaces stale/read-only without stopping customer delivery.

- [ ] P07.1 Add connector install preview, scope review, mapping queue, health, lag, and revoke impact.
- [ ] P07.2 Add webhook/polling reconciliation for missed, duplicate, and out-of-order events.
- [ ] P07.3 Show provider permissions separately from ShipSense permissions at action points.
- [ ] P07.4 Build connector failure, rate-limit, reconnect, and backfill operator paths.
- [ ] P07.5 Run an outage drill proving external CI/CD continues and history is reconciled.

### P08 — Alerts and incident command · Not started
**Prerequisite:** P05–P07. **Exit:** an alert produces a time-frozen incident with evidence, ownership, and communication state.

- [ ] P08.1 Ingest Slack/generic alert signals, deduplicate transparently, and support audited split/merge.
- [ ] P08.2 Build incident workspace with severity, roles, timeline, impact, actions, and reviewed updates.
- [ ] P08.3 Freeze topology, changes, telemetry links, coverage, and source freshness for the incident window.
- [ ] P08.4 Track mitigation, monitoring, observed recovery, and owner-confirmed resolution.
- [ ] P08.5 Exercise external-provider outage and mixed-cause scenarios.

### P09 — Application-scoped AI copilot · Not started
**Prerequisite:** P02–P08. **Exit:** cited explain/compare answers preserve scope and abstain on denied or stale decisive sources.

- [ ] P09.1 Implement visible context capsule for tenant, service, environment, time, role, and source coverage.
- [ ] P09.2 Build authorized source planner with cost/time/data budgets and cancellation.
- [ ] P09.3 Use LangGraph for resumable turns and LangChain adapters where useful; persist scoped checkpoints in MongoDB.
- [ ] P09.4 Use OpenAI API behind a model adapter; require structured claim/evidence outputs and log version/cost.
- [ ] P09.5 Display facts, interpretations, contradictions, gaps, confidence limits, source links, and correction history.
- [ ] P09.6 Test cross-tenant leaks, injected logs/runbooks, revoked access, stale memory, and tool failures.

### P10 — AI evidence investigator · Not started
**Prerequisite:** P09. **Exit:** a failed run or incident yields a reviewable multi-hypothesis report or explicit abstention.

- [ ] P10.1 Freeze investigation scope, source versions, topology, and budget.
- [ ] P10.2 Collect authorized code, CI, release, runtime, telemetry, alert, and knowledge evidence.
- [ ] P10.3 Rank multiple plausible hypotheses with support, disconfirmation, contradiction, and missing evidence.
- [ ] P10.4 Cap confidence by coverage and source quality; stop on insufficient evidence.
- [ ] P10.5 Let users challenge claims and persist report/evidence manifest for audit and replay.

### P11 — Governed remediation and verification · Not started
**Prerequisite:** P02, P05, P10. **Exit:** approved minimal patch opens a verified draft PR; unsafe proposals stop before effects.

- [ ] P11.1 Define action proposal states, exact scope, path/dependency budget, expiry, and rollback plan.
- [ ] P11.2 Isolate candidate changes and verification jobs from production credentials and tenant data.
- [ ] P11.3 Run formatting, lint, type, tests, security, secret, policy, and unrelated-diff checks.
- [ ] P11.4 Show evidence chain, alternatives, exact diff, checks, approver, and provider authority.
- [ ] P11.5 Open draft GitHub PR after eligible review; human/provider permissions control merge.
- [ ] P11.6 Observe merge through CI, rollout, SLO, and incident recovery; classify healthy/regressed/inconclusive.

### P12 — Replay and evaluation lab · Not started
**Prerequisite:** P09–P11. **Exit:** fixed cases reproduce outcomes and an unsafe regression blocks a release.

- [ ] P12.1 Convert synthetic or consented incidents into sanitized, tenant-isolated fixtures in R2.
- [ ] P12.2 Freeze expected evidence, causes, prohibited actions, abstention, and version metadata.
- [ ] P12.3 Replay model/prompt/tool/policy versions under identical inputs with hidden labels.
- [ ] P12.4 Report citation precision/coverage, contradiction, cause rank, abstention, safety, cost, and latency.
- [ ] P12.5 Gate releases on zero authorization leakage/policy bypass/unsafe actions and specified quality thresholds.

### P13 — Release 1 integration and readiness · Not started
**Prerequisite:** P01–P12. **Exit:** acceptance journeys for the trustworthy loop pass across roles and failure states.

- [ ] P13.1 Run end-to-end failed-run and alert-to-verified-PR scenarios on the reference demo service.
- [ ] P13.2 Review keyboard accessibility, role permissions, partial data, and stale provider states.
- [ ] P13.3 Measure setup time, time to decisive evidence, user comprehension, and AI evaluation gates.
- [ ] P13.4 Publish runbooks, Swagger docs, architecture decisions, threat model, and recovery demo.
- [ ] P13.5 Record explicit release decision with gaps and evidence; archive a replay baseline.

### P14 — Jenkins and Kubernetes/Argo delivery breadth · Not started
**Prerequisite:** P13 and connector contract. **Exit:** Jenkins runs and Kubernetes/Argo delivery state have full source links and authorized actions.

- [ ] P14.1 Extend Release 1 Jira integration with release/version identity, complex field mappings, and larger backfills.
- [ ] P14.2 Connect read-first Kubernetes inventory and Argo CD/Rollouts desired, observed, drift, and progressive rollout history.
- [ ] P14.3 Connect Jenkins jobs/builds/stages/tests/artifacts and map retries and parameters into canonical CI states.
- [ ] P14.4 Add manual trigger/cancel/retry and AI proposal handoff through the same action framework.
- [ ] P14.5 Validate denied scopes, rate limits, failure recovery, and parity with GitHub Actions flows.

### P15 — Remaining managed deployment providers and release command · Not started
**Prerequisite:** P03, P06, P11, P13. **Exit:** each supported provider exposes honest capability labels, safe manual controls, and verified outcomes.

- [ ] P15.1 Extend the Release 1 Azure/Vercel deployment adapter contract to Netlify, Railway, and Render with a per-provider capability matrix.
- [ ] P15.2 Map deployment, environment, artifact/revision, config metadata, logs, and provider receipts.
- [ ] P15.3 Add authorized trigger/promote/hold/rollback controls only where provider semantics support them.
- [ ] P15.4 Build release candidate, immutable artifact identity, policy checks, approvals, environment parity, and change window views.
- [ ] P15.5 Verify actual post-deploy health and distinguish deploy success from customer recovery.

### P16 — Security and advanced delivery · Not started
**Prerequisite:** P11, P15. **Exit:** exact artifact and production decisions are explainable and governed.

- [ ] P16.1 Ingest SAST/SCA/secrets/IaC findings; link SBOM, digest, signature, and provenance.
- [ ] P16.2 Add scoped security exceptions with owner, rationale, compensating control, and expiry.
- [ ] P16.3 Add multi-service release trains, migration compatibility, feature flags, and environment drift.
- [ ] P16.4 Add canary/blue-green analysis, abort, rollback versus fix-forward, and health verification.
- [ ] P16.5 Evaluate predictive change risk and incident scribe only after AI trust and noise gates pass.

### P17 — Engineering intelligence · Not started
**Prerequisite:** P13–P16. **Exit:** metrics drill to source data with disclosed definitions and coverage.

- [ ] P17.1 Compute current DORA metrics and SLO/incident trends with definition/version controls.
- [ ] P17.2 Add flaky test, rework, automation acceptance, abstention, and false-positive measures.
- [ ] P17.3 Add role-scoped dashboards and exports; avoid individual productivity scoring.
- [ ] P17.4 Add cost attribution for AI, storage, telemetry queries, and connectors.
- [ ] P17.5 Review metrics against golden data and missing-source scenarios.

### P18 — Enterprise governance and resilience · Not started
**Prerequisite:** P02, P07, P13. **Exit:** tenant lifecycle, large-scale access, and product disaster recovery have tested evidence.

- [ ] P18.1 Add enterprise SSO/provisioning profile and customer-side/private connector option where validated.
- [ ] P18.2 Add data residency, retention, export/deletion, legal-hold, and audit archive controls.
- [ ] P18.3 Add quotas, billing/usage visibility, support bundles, feature flags, and AI/tool kill switches.
- [ ] P18.4 Rehearse backup/restore, credential rotation, replay reconciliation, and RPO/RTO reporting.
- [ ] P18.5 Run load, security, privacy, accessibility, and cross-tenant isolation reviews.

### P19 — Full-product validation and portfolio handoff · Not started
**Prerequisite:** P14–P18. **Exit:** all applicable acceptance journeys and release gates have reproducible evidence.

- [ ] P19.1 Demonstrate failure, abstention, blocked unsafe action, approved proposal, observed recovery, and replay regression.
- [ ] P19.2 Run task studies for developer, SRE, platform, security, and leadership roles.
- [ ] P19.3 Compare investigation time and evidence quality with existing tools using the same scenario.
- [ ] P19.4 Document remaining product gaps, operations manual, architecture, API, model evaluation, and lessons.
- [ ] P19.5 Decide commercial validation separately through interviews and design partners.

## Cross-phase rules

Every feature must carry tenant/service/environment/time scope; provider identity and freshness; authorization at the API and connector; loading/empty/stale/denied/failure states; audit; tests for meaningful failure paths; and a source link when a claim depends on external evidence. A phase may run in parallel with another only when its stated prerequisites and shared contracts are ready. Jira tracks work; `PROJECT_STATUS.md` records phase truth and proof.

## Execution choices at later gates

1. P01 validates Central India, Atlas tier, service availability, tenancy setup, OIDC issuer, R2 retention classes, and the itemized forecast before paid provisioning.
2. P05–P06 pin provider-specific capabilities and effect permissions.
3. P12 selects the initial OpenAI model and evaluation set using quality, latency, cost, and data-handling measurements.
4. Set milestone and sprint dates after team capacity, provider access, and pilot availability are known.
