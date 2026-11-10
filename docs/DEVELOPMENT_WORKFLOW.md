# ShipSense development workflow

Use phase/subphase acceptance checkpoints (`P0X.YY`) from [the phase index](../Phases/README.md). [Decision 0008](decisions/0008-checkpoint-development-workflow.md) replaces the former development tracker and key-validation policy. The customer-facing Jira connector remains in product scope.

Select the smallest ready checkpoint, read its prerequisites and criteria, and record concrete proof in [project status](../PROJECT_STATUS.md) and the relevant GitHub PR. Related checkpoints may share a branch, commits and PR when dependencies and review risk permit; report acceptance separately for each. Use descriptive names with checkpoint references, such as `feature/P01.5-hosted-configuration` and `P01.5: verify hosted configuration and clean integration`. Existing published legacy branch names may remain until their PR lands; do not rewrite history solely to rename them.

Install the staged Markdown hook with `git config core.hooksPath .githooks`. Complete affected required local checks and direct behavior proof before publication. Audit all proposed files, keep secrets and disposable evidence outside the product tree, then verify required current-head remote checks. Independent exact-current-SHA review and acceptance remain required. Findings return to the author; clearance proceeds to acceptance. Routine accepted low-risk merges follow Decision 0004; risky or complex merges require owner review. Phase completion requires every applicable checkpoint and the phase exit proof, separately from merging.

No development Jira connection, issue, epic, sprint, naming key, Development-panel link or Jira status check is required. Do not administer Jira for this repository or revoke shared Atlassian access used by other projects.
