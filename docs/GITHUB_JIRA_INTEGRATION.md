# GitHub and Jira development sync

**Updated:** 23 October 2026. GitHub for Atlassian is connected to `spjyotiranjan/shipsense`. [SCRUM-13](https://spjyotiranjan.atlassian.net/browse/SCRUM-13) shows one branch, three commits, and an open PR in Jira's Development panel. The open PR and source branch both link to GitHub from that panel. GitHub does not automatically turn an unbracketed issue key in every PR title or branch listing into a Jira hyperlink. A bracketed key in a GitHub comment, such as `[SCRUM-13]`, is expanded by the Atlassian app.

## Development rule

Use one Jira work item per pull request. Include the same `SCRUM-<positive issue number>` key anywhere in the branch name, each commit message, and the PR title. The key may appear at the beginning, middle, or end:

| Place | Example |
| --- | --- |
| Branch | `feature/SCRUM-14-add-quality-hooks` |
| Commit message | `Add quality hooks for SCRUM-14` |
| PR title | `Add quality hooks (SCRUM-14)` |

The key belongs to the work item for the actual change. Do not use a convenient existing key or a phase epic key. The GitHub for Atlassian app uses these keys to link development events to Jira. Mentioning a sprint name alone does not create a development link. GitHub's `SCRUM-` numeric autolink points to this Jira site; plain keys in PR descriptions and commit entries are clickable. The Atlassian bot also makes a bracketed key in a GitHub comment clickable, for example `[SCRUM-14]`.

## Local Markdown lint

Run `git config core.hooksPath .githooks` once in each clone. The remaining `pre-commit` hook checks staged Markdown for trailing whitespace and a final newline. The local branch and commit-key scripts and their hooks were removed; Jira owns the development-key validation described below. The PR template still repeats the shared-key rule.

## Jira-owned PR status

The enabled [Jira PR validation flow](https://spjyotiranjan.atlassian.net/jira/software/projects/SCRUM/settings/automation#/rule/01a1685b-482c-7d7b-b86e-eaa73a9a620e) listens for a connected PR creation event. It limits processing to `spjyotiranjan/shipsense`, requires the PR title and source branch to contain the linked Jira key, fetches the GitHub PR and up to 100 commits, requires the fetched count to equal the PR commit count, and compares every fetched commit message's issue key with that linked Jira key. Only after those guards does Jira post the `jira/shipsense-pr-link` success status to the PR head SHA. A PR with more than 100 commits cannot pass this flow until pagination is implemented.

The two GitHub Actions Jira/branch validation workflows were removed because Jira now owns those checks. `JIRA_EMAIL` and `JIRA_API_TOKEN` GitHub repository secrets are no longer used for them. The Jira automation has its own GitHub status credential, kept hidden in Jira; never copy that credential into this repository. The flow is triggered by PR creation, so a title edit without a new head SHA is not yet revalidated. A new push gets a new SHA with no inherited success, but this flow does not currently run on synchronize. **Do not make this Jira status a required merge check until a PR creation, title edit, and new-push test have each produced the expected status behavior.** No such end-to-end run was observed after adding the commit guards.

## Verify development sync

1. Create a branch for an existing ShipSense subphase work item and make a commit with its key in the subject.
2. Open a PR with the same key anywhere in its title. Check that Jira's Development page lists the PR and that the work item's Development panel shows its branch, commits, and PR.
3. For a clickable Jira link inside GitHub, use a bracketed issue key in a PR comment, for example `[SCRUM-14]`, or put the full Jira issue URL in the PR body. The issue's Development panel is the evidence that the PR and branch are associated with it.
4. Inspect the Jira PR validation flow's audit log and the `jira/shipsense-pr-link` commit status on a new PR. Verify a wrong branch key, a wrong commit key, and a missing key do not produce success. Check the count guard for a PR with more than 100 commits before relaxing that limit.
5. Check the separate [PR-created to In Review flow](https://spjyotiranjan.atlassian.net/jira/software/projects/SCRUM/settings/automation#/rule/01a16826-1bf3-7162-86a1-a7eed71250c8). It applies only to P01/P02 labelled items already **In Progress**. A merge or deployment does not mark acceptance complete or move an issue to Done.

GitHub Actions workflow and deployment events can also be linked by the app when their associated commits carry the key. Azure build and deployment checks will be configured separately in the deployment phase. This GitHub/Jira connection is distinct from the Release 1 customer-facing Jira connector planned for P05.
