# GitHub and Jira development sync

**Updated:** 23 October 2026. Jira's ShipSense Development page shows GitHub for Atlassian connected to `spjyotiranjan`. The owner selected **All repositories** during authorization; that repository scope has not been independently inspected. No ShipSense commit or PR has yet been observed on a Jira work item's Development panel. The pull-request-created automation flow remains disabled until that end-to-end check passes.

## Development rule

Use one Jira work item per pull request. The branch name, every commit subject, and PR title must carry the same exact `SCRUM-<number>` key. Put the key at the start of each commit subject and PR title:

| Place | Example |
| --- | --- |
| Branch | `SCRUM-14-add-quality-hooks` |
| Commit subject | `SCRUM-14 Add quality hooks` |
| PR title | `SCRUM-14 Add quality hooks` |

The key belongs to the work item for the change. Do not use a phase epic key as a substitute for a subphase task. The GitHub for Atlassian app uses these keys to link development events to Jira. Mentioning a sprint name alone does not create a development link.

## Commit-time checks

Run `git config core.hooksPath .githooks` once in each clone. The tracked hooks then run on commit:

- `pre-commit` checks staged Markdown for trailing whitespace and a final newline.
- `commit-msg` requires the subject to start with `SCRUM-<number>`.

These hooks do not call Jira and need no Jira API token. Git hooks are local safeguards; contributors can bypass them, so the team still reviews PR titles and checks that the development link appears in Jira. The PR template repeats the title rule. A future repository ruleset can require the Azure build check when that workflow exists.

## Verify development sync

1. Create a branch for an existing ShipSense subphase work item and make a commit with its key in the subject.
2. Push the branch and open a PR whose title starts with the same key.
3. Open that Jira work item and verify the branch, commit, and PR appear in its Development panel. The ShipSense Development page should then list the repository and PR.
4. Check the Jira automation audit log. Enable the [PR-created → In Review flow](https://spjyotiranjan.atlassian.net/jira/software/projects/SCRUM/settings/automation#/rule/01a16826-1bf3-7162-86a1-a7eed71250c8) after a linked PR event is observed. It applies only to labelled P01/P02 work items already **In Progress**. Do not move a phase backlog item to In Progress merely to test the flow.
5. For a later qualifying PR, verify the flow transitions only its linked work item to **In Review**. A merge or deployment does not mark acceptance complete or move a work item to Done.

GitHub Actions workflow and deployment events can also be linked by the app when their associated commits carry the key. Azure build and deployment checks will be configured separately in the deployment phase. This GitHub/Jira connection is distinct from the Release 1 customer-facing Jira connector planned for P05.
