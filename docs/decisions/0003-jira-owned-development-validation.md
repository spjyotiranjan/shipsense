# Decision 0003: Jira owns ShipSense development validation

**Date:** 23 October 2026
**Status:** Accepted for current repository workflow; live commit-guard proof pending

## Decision

Use the GitHub for Atlassian development connection and the Jira PR-created automation to associate and validate ShipSense PRs. The Jira flow checks the linked issue key in the PR title, source branch, and every fetched PR commit message before posting `jira/shipsense-pr-link` success to the head commit. Remove the duplicate GitHub Actions branch/Jira issue workflows and their need for `JIRA_EMAIL` and `JIRA_API_TOKEN` secrets. Remove local branch and commit-key scripts and hooks; retain only the staged Markdown lint hook.

## Constraints and proof still needed

- Jira's issue Development panel is the association evidence. The PR and branch for SCRUM-13 are linked there. GitHub's display of an issue key as a hyperlink is separate; a bracketed key in a GitHub comment or full Jira URL in the PR body provides a backlink.
- The Jira flow reads at most 100 PR commits and compares the fetched count with the PR's reported commit count. Larger PRs fail closed until pagination is added.
- The flow fires on PR creation. It does not yet rerun when a title changes or commits are pushed. Do not require its status for merging until those lifecycle paths are covered and verified on live PRs.
- The newly added commit guard has been saved in the enabled Jira rule, but no post-change PR event has run through it. Verify the audit log and GitHub status with valid and invalid commit messages before treating it as proven.
- Adding a Jira-authored comment to a GitHub PR requires a separate Atlassian Automation GitHub connection. The current GitHub for Atlassian development connection does not supply that action automatically.

## Evidence

- [SCRUM-13 Development panel](https://spjyotiranjan.atlassian.net/browse/SCRUM-13): one branch, three commits, and an open PR were visible on 23 October 2026.
- [Jira PR validation flow](https://spjyotiranjan.atlassian.net/jira/software/projects/SCRUM/settings/automation#/rule/01a1685b-482c-7d7b-b86e-eaa73a9a620e): enabled and saved with PR title, branch, commit-count, and per-commit key guards.
- `docs/GITHUB_JIRA_INTEGRATION.md` records current setup and verification steps.
