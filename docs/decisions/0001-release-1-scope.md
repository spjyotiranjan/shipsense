# Decision 0001 — Release 1 scope and acceptance

**Date:** 23 October 2026
**Status:** Accepted for integration breadth and operating scale; region and spending cap are provisional execution controls.
**Decision owner:** ShipSense project owner.

## Decision

Release 1 covers the end-to-end ShipSense trust loop across **GitHub, GitHub Actions, Jira, Azure deployments, and Vercel deployments**. Jira is both the development tracker and a customer-facing connector; those are separate configurations. Azure hosts ShipSense itself. Azure and Vercel connectors show deployment, revision, environment, provider receipt, and observed health for connected customer services. OpenTelemetry-based signals, source-linked metrics, and generic webhook alerts supply minimum runtime evidence.

The journey is: open a failed PR run or alert for one service; inspect the time-scoped change, CI, Jira, deployment and telemetry trail; ask a bounded question; review competing hypotheses and contradictions; obtain a minimal verified draft PR under policy and human review; observe post-merge health; freeze a resolved case for replay. AI cannot directly mutate production.

Use OpenTelemetry Astronomy Shop as the initial reference application. P01 pins one primary service and named fixtures. Seed pipeline failure, probe/config regression, missing telemetry, dependency failure, injected runbook, and deployment regression. Azure and Vercel may host separate small reference deployments if a single workload is impractical on both.

### Delivery order

1. P01–P04: repository, identity, canonical evidence, catalog.
2. P05: GitHub, Actions, Jira issue links and governed issue updates.
3. P06: Azure and Vercel deployment evidence, revision lineage, bounded telemetry, health/SLO views.
4. P07–P12: continuity, incidents, copilot, investigation, governed remediation, replay.
5. P13: cross-provider Release 1 acceptance.

Jenkins, Netlify, Railway, Render, Kubernetes/Argo CD/Rollouts connectors, enterprise identity, and advanced delivery controls remain later milestones. Shared contracts are designed early.

## Identity, location, and spending

- **Identity:** OIDC login with a local development issuer selected in P01; FastAPI and workers enforce tenant, role, service, environment and action permissions independently of the web session. SAML/SCIM remains P18.
- **Initial Azure region:** Central India is a provisional default, not a user-selected residency commitment. P01 validates Azure service and Atlas tier availability, latency to R2/Vercel, and pilot residency needs before provisioning. If these checks fail, record a region change.
- **Operating target:** 20–30 active users with a properly configured product. Measure p95 latency, queue lag, investigation duration and monthly consumption under representative load before scaling.
- **Cost control:** The owner supplied no monetary ceiling. Do not invent one. Before paid provisioning, produce an itemized monthly forecast for Azure, Atlas, R2, Vercel, telemetry and OpenAI; choose the smallest production-suitable tiers; set budgets/alerts and AI/query/storage quotas; obtain a spending decision if the forecast exceeds the owner's preferred limit. Track cost per investigation and active user in P12/P17.

## Measurable Release 1 gates

P12 pins a fixed reviewed fixture set and method. Initial product-specification targets are evidence precision ≥0.90 and recall ≥0.80; root-cause top-3 ≥0.85 and top-1 ≥0.65; contradiction coverage ≥0.80; abstention precision ≥0.85; supported-pattern patch applicability ≥0.90; unrelated-change rate ≤0.02; conversation scope accuracy ≥0.98 with zero cross-tenant cases; answer citation coverage ≥0.95 and 1.00 for action-driving claims. Unsafe action, policy bypass, and authorization leakage counts must each be zero. These are evaluation targets, not general model-accuracy promises.

P13 demonstrates GitHub → Actions → Jira → Azure and GitHub → Actions → Jira → Vercel traceability; failed-run and alert investigations; a blocked unsafe proposal; approval invalidation after material change; a verified draft PR; observed health distinct from deploy success; and a replay regression blocking promotion. Partial, stale, denied and provider-outage states and keyboard-accessible review are in scope.

## Consequences

This breadth requires more connector work than the earlier focused proposal. Keep connectors read-first and capability-labeled, reuse canonical contracts, and require cross-provider proof before Release 1. P01 owns region feasibility and a cost forecast. The owner approves actual recurring spend before paid provisioning.
