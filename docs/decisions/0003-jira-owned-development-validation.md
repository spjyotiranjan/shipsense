# Decision 0003 — Former development validation

**Date:** 23 October 2026
**Status:** Superseded for development by [Decision 0008](0008-checkpoint-development-workflow.md), 10 November 2026.

## Historical decision

The original workflow used Jira-owned PR validation and development linkage instead of duplicate GitHub Actions and local issue-key validators. It had a 100-commit limit and unverified title-edit/new-push lifecycle behavior. Those were historical implementation limits, not current acceptance gates. The staged Markdown hook was retained.

## Replacement

ShipSense development now uses phase/subphase checkpoints, descriptive names and GitHub/source evidence. There is no active Jira development connection, administration, naming, validation or linkage requirement. Retired setup links and connection instructions have been removed. Preserve published commit/PR history; do not rewrite it to scrub old names. Customer-facing Jira integration remains separate and unchanged in scope.
