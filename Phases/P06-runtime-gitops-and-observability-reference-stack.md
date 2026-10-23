# P06 — Azure and Vercel deployments with observability

**Current status:** Not started. Update `../PROJECT_STATUS.md` with evidence when it changes.
**Prerequisites:** P03–P05.
**Phase outcome:** service view links exact Azure and Vercel deployed revisions, deployment state, runtime fault, and SLO signal.

## Purpose and scope

Connect Azure and Vercel deployments to actual runtime and reliability signals.

**Included:** Azure and Vercel deployment adapters, OpenTelemetry and source-linked metrics, SLOs, supported manual controls, and failure fixtures.
**Critical failure boundary:** Missing telemetry must halt automatic confidence or promotion.

## Overall phase acceptance

- The phase outcome is demonstrated: Service view links exact Azure and Vercel deployed revisions, state, runtime fault, and SLO signal.
- Every subphase below satisfies its acceptance criteria and has a linked proof artifact, such as a passing test, screenshot, API contract, decision record, provider receipt, or Jira issue.
- Permissions, tenant and environment scope, source provenance, freshness, accessible states, audit, and meaningful failure paths are checked wherever the phase touches them.
- The parent phase is marked Complete only after the exit review records reviewer, date, evidence links, unresolved gaps, and any follow-on work.

## Subphases

### P06.1 — Connect Azure deployments, revisions, runtime state, and history

**Status:** Not started.
**Expected result:** Map Azure service/environment, deployed revision, configuration metadata, health and provider history with source links.

**Acceptance criteria**

- Azure fixture displays exact revision, deployment status, instance/health signal, configuration metadata without secret values, provider receipt, owner, and observation time. Manual controls appear only when supported and authorized.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P06.2 — Connect Vercel deployments, revisions, environments, and history

**Status:** Not started.
**Expected result:** Map Vercel project/environment, deployment, source revision, readiness, logs, and provider history with source links.

**Acceptance criteria**

- Vercel fixture distinguishes build/deploy success from healthy customer outcome, links exact Git revision and provider deployment, and exposes only supported authorized controls.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P06.3 — Connect bounded OpenTelemetry and source-linked metrics/traces

**Status:** Not started.
**Expected result:** Connect OpenTelemetry and source-linked metrics/traces through bounded queries; use Grafana where the reference installation exposes it.

**Acceptance criteria**

- Bounded telemetry queries link to original traces/metrics; partial windows and source lag are visible and query budgets enforced.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P06.4 — Define SLIs/SLOs, error-budget views, burn alerts, and release overlays

**Status:** Not started.
**Expected result:** Define SLIs/SLOs, error-budget views, burn alerts, and release overlays.

**Acceptance criteria**

- SLI/SLO and burn calculations match golden data with declared windows and deployment overlays.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

### P06.5 — Demonstrate Azure/Vercel regressions and explicit missing telemetry

**Status:** Not started.
**Expected result:** Demonstrate probe/config failure, Azure and Vercel deployment regression, and explicit missing telemetry.

**Acceptance criteria**

- Probe/config failure, Azure and Vercel regressions, and missing data each produce distinct UI and policy outcomes; missing telemetry never becomes automatic success.
- The result can be inspected by another contributor without relying on an unstated local setup or private explanation.
- A representative failure, denial, missing-data, or recovery case is recorded when this subphase handles external data or effects.

**Proof to attach:** Link the implementation or decision, its targeted verification result, and any UI/provider/audit evidence in the Jira item and `../PROJECT_STATUS.md`.

## Phase review record

- Reviewer and date: _pending_
- Evidence links: _pending_
- Open risks and owner: _pending_
- Decision: _pending_
