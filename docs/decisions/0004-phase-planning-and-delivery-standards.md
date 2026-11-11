# Decision 0004 — Phase planning and delivery standards

**Development workflow supersession — 10 November 2026:** [Decision 0008](0008-checkpoint-development-workflow.md) replaces development-tracking, naming, linkage and administration requirements. Product connector scope and technical quality gates remain in force.

**Date:** 8 November 2026
**Amendment date:** 9 November 2026
**Status:** Accepted.
**Decision owner:** ShipSense project owner.

## Planning and technical boundaries

Prepare phase-specific technical web and backend implementation plans in docs/web-implementation/ and docs/backend-implementation/ before implementation, with the owner's audit and go-ahead. Maintain one plan per area per phase; individual checkpoints follow those plans. Revisit planning only when a new finding requires an adjustment. Plans contain technical development scope, dependencies, contracts, acceptance and verification; exclude staffing, internal organization and coordination details. Include accepted plans and these deferred standards in the first working implementation commit and PR; no separate planning commit or PR.

Python FastAPI is the main backend for canonical domain behavior, authorization and orchestration. Next.js API routes provide the normal web-facing backend layer and call FastAPI for canonical behavior, as established by Decision 0002.

## UI scope

Use a simple, functional and consistent UI while broad product coverage is being built. UI libraries are permitted within the accepted stack. A full redesign follows broad product coverage and a whole-app design. Accessibility, degraded states, security and meaningful failure verification still apply.

## Delivery

Related checkpoints may share descriptive branches, commits and PRs; retain evidence and acceptance for each checkpoint under Decision 0008.

Accepted coding work is complete after required local checks and direct behavior proof, independent exact-current-SHA review and acceptance. It does not wait for the owner’s PR review or merge. Routine low-risk changes are merged automatically after these gates and required remote checks; risky or complex merges require owner review. This replaces the prior owner-only manual-merge policy. Preserve permission boundaries, spending approval and all quality gates.

## Repository hygiene

Keep the repository, commits and PRs limited to implementation and durable technical documentation/configuration needed to develop, run and maintain the product. Store disposable review captures, verification logs, temporary helpers and scratch files outside the product tree; link evidence from delivery work items. Product image assets and intentional test fixtures remain implementation assets. Inspect tracked/untracked files and the complete staged and proposed PR file lists before delivery; add narrow ignore protection. Preserve required technical plans, architecture decisions and status records while excluding internal coordination logs.

## Rationale and sources

Keep implementation plans technical and distinguish accepted implementation from merged delivery.

- Phase plans/first-working-commit direction: PAT-104 user comments ec23ba40-e83c-4a20-bf1c-82de8f29308f and 0865e7ec-59d8-411a-9453-540abc29ded6, retained in Project Context.
- Simple UI and later redesign: user comment 9a239182-8fe8-41ca-83b8-43414e55ef2f, retained in Project Context.
- One planning cycle per phase: user comment 7e654688-5f57-4cab-b351-de1f3c8922d1.
- Technical-only plans and FastAPI boundary: user comment 22eff537-c603-417c-a3d0-eaadcc186317.
- Approval after corrections: user comment 95bce72c-2d9d-4a07-a584-142e48927225 applies to the corrected P01 plans; future phase audit gates remain.
- Delivery policy amendment: authenticated user source e2ec3e8b-9c11-459f-81c4-71ee03b87719, 9 November 2026; replaces the prior owner-only manual-merge policy.
- Repository hygiene: authenticated user direction, 8 November 2026, source comment ab0231ad-0ae0-449b-bb6e-7d161bf7578f.
