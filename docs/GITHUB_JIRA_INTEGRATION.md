# GitHub and Jira development sync

**Updated:** 23 October 2026. Jira's Development page shows GitHub for Atlassian connected to `spjyotiranjan` and lists `spjyotiranjan/shipsense`. The owner selected **All repositories** during authorization; that scope has not been independently inspected. A temporary PR appeared in Jira's Development pull-request list, and its branch and commit appeared on a Jira work item. That issue's Development panel did not show the PR. Atlassian's bot turned a bracketed issue key in a PR comment into a clickable Jira link. The temporary PR and branch were removed after this connection test. The Jira PR-created automation is enabled for future events; its audit log has no trigger run yet.

## Development rule

Use one Jira work item per pull request. The branch name, every commit subject, and PR title must carry the same exact `SCRUM-<number>` key. Put the key at the start of each commit subject and PR title:

| Place | Example |
| --- | --- |
| Branch | `SCRUM-14-add-quality-hooks` |
| Commit subject | `SCRUM-14 Add quality hooks` |
| PR title | `SCRUM-14 Add quality hooks` |

The key belongs to the work item for the actual change. Do not use a convenient existing key or a phase epic key. The GitHub for Atlassian app uses these keys to link development events to Jira. Mentioning a sprint name alone does not create a development link. GitHub's `SCRUM-` numeric autolink points to this Jira site; plain keys in PR descriptions and commit entries are clickable. The Atlassian bot also makes a bracketed key in a GitHub comment clickable, for example `[SCRUM-14]`.

## Commit-time checks

Run `git config core.hooksPath .githooks` once in each clone. The tracked hooks then run on commit:

- `pre-commit` checks staged Markdown for trailing whitespace and a final newline.
- `commit-msg` requires the subject to start with `SCRUM-<number>`.

These hooks do not call Jira and need no Jira API token. Git hooks are local safeguards; contributors can bypass them, so the team still reviews PR titles and checks that the development link appears in Jira. The PR template repeats the title rule.

## GitHub merge check

`.github/workflows/jira-issue-check.yml` runs on future PRs. Its `Jira issue verified` job requires a title beginning with `SCRUM-<number>` and reads that work item from this Jira site's REST API. Success proves the key exists and the GitHub job reached Jira. It does not prove that the PR appears in the issue's Development panel or that Jira automation ran.

The repository owner must add `JIRA_EMAIL` and `JIRA_API_TOKEN` as GitHub Actions repository secrets using an Atlassian account with Browse access to ShipSense. Keep the token out of commits and tickets. After the first successful run, add `Jira issue verified` as a required status check in the `main` branch ruleset alongside the Azure build job once it exists. Until the secrets and ruleset are configured, GitHub does not block merges on this check. Direct pushes to `main` do not run this PR workflow.

## Verify development sync

1. Create a branch for an existing ShipSense subphase work item and make a commit with its key in the subject.
2. Open a PR with the same key at the start of its title. Check that Jira's Development page lists the PR and that the work item's Development panel shows its branch, commits, and PR.
3. For a clickable Jira link inside a GitHub comment, use brackets such as `[SCRUM-14]`. A comment link alone does not prove issue-panel linkage.
4. Check the [PR-created to In Review flow](https://spjyotiranjan.atlassian.net/jira/software/projects/SCRUM/settings/automation#/rule/01a16826-1bf3-7162-86a1-a7eed71250c8) audit log. It is enabled and applies only to P01/P02 labelled work items already **In Progress**. The temporary test PR predates activation and cannot demonstrate a trigger run. Do not move a backlog item to In Progress merely to test it.
5. For the next qualifying PR, verify that only its linked issue moves to **In Review**. A merge or deployment does not mark acceptance complete or move an issue to Done.

GitHub Actions workflow and deployment events can also be linked by the app when their associated commits carry the key. Azure build and deployment checks will be configured separately in the deployment phase. This GitHub/Jira connection is distinct from the Release 1 customer-facing Jira connector planned for P05.
