# Decision 0008 — Checkpoint development workflow

**Date:** 10 November 2026
**Status:** Accepted; supersedes development-tracking requirements in Decisions 0001–0004 and 0006 and the former development workflow documents.
**Decision owner:** ShipSense project owner.

## Decision

ShipSense development uses phase/subphase acceptance checkpoints (`P0X.YY`, for example `P01.5`). Multiple related checkpoints may share a branch, commits and pull request when dependencies, review scope and risk permit. Use descriptive names with checkpoint references and retain separate acceptance evidence for every checkpoint.

Jira is not used for ShipSense development. No Jira development connection, epic, sprint, task administration, issue-key naming, Development-panel linkage or remote key-validation gate is required. Do not call Jira to administer or validate this repository. Published history need not be rewritten to remove legacy names; existing open PR branches may retain their names to preserve review tracking. New names use checkpoints.

This change preserves the customer-facing Jira connector and its Release 1 product requirements. Shared Atlassian credentials/connections used by other projects must not be revoked. Historical accepted technical proof remains revision/profile-specific; replacing its tracking reference does not create new acceptance or prove hosted operation.

## Gates retained

Keep phase technical plans, prerequisite checks, the Markdown pre-commit hook, required local checks and direct behavior proof before publication, required remote checks, independent exact-current-SHA review and acceptance. Preserve permission, production-effect, spending and risk-based merge gates. Related checkpoints sharing a PR does not waive their individual criteria. A green build, merged PR or closed work item alone does not complete a checkpoint or phase.

See [development workflow](../DEVELOPMENT_WORKFLOW.md) and [project status](../../PROJECT_STATUS.md).

## Source and rationale

Authenticated project-owner direction, 10 November 2026, source comment `21bb6dc5-e4db-4201-8edc-f81a37836331`. Checkpoints provide the acceptance structure directly without a separate development tracker. Canonical transcription was delegated in the current implementation change; this decision changes development workflow only.
