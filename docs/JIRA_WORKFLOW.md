# Jira phase, epic, and sprint workflow

**Decision from project owner, 23 October 2026:** Create an epic for a phase **when that phase starts**, and create its sprint at the same time. The sprint comprises **all subphases of that phase**. Do not pre-create epics or sprints for future phases.

## Mapping

| ShipSense record | Jira record |
| --- | --- |
| Phase Pxx | One epic titled `Pxx — <phase title>` |
| Phase sprint | One sprint on ShipSense Scrum board containing every subphase; preferred title `ShipSense Pxx — <phase title>` |
| Subphase Pxx.n | One task/story in the epic and sprint, titled `Pxx.n — <subphase title>` |
| Acceptance evidence | Issue description/checklist and links to tests, decisions, API contract, UI proof, or provider receipt |
| Cross-phase prerequisite | Issue or epic link `is blocked by`; prerequisites are noted in backlog tasks; link blockers when the phase starts |

## Start a phase

1. Verify prerequisites and record the phase start date in `PROJECT_STATUS.md`. A phase owner, team assignments and estimates may be added manually later.
2. Create the phase epic and sprint together. Use the prepared backlog tasks, create any missing subphase task, link all of them to the new epic, and put every subphase in that sprint.
3. Copy each subphase's expected result and acceptance criteria from `Phases/Pxx-*.md`, adding dependencies and evidence links. Owners and estimates can be entered manually later. Do not mark an issue done solely because a document exists.
4. Record the Jira project key, board ID, epic key, sprint ID, and subphase issue keys in the phase file or a linked status record.
5. The team sets sprint dates, goal refinement, estimates and assignments manually. Only the user starts a sprint under the existing team working agreement; creating a sprint does not start it. If a subphase is blocked, keep it visible in the same sprint and link the blocker; replan dates transparently.

P00 is complete. P01 and P02 have separate preplanned backlogs. The P00 records use Jira site `https://spjyotiranjan.atlassian.net`, existing space **ShipSense** (key `SCRUM`), Scrum board `1`, epic [SCRUM-6](https://spjyotiranjan.atlassian.net/browse/SCRUM-6), and unstarted sprint `35`. Jira currently displays sprint 35 as **SCRUM Sprint 2**: two attempts to rename it appeared to succeed locally, but reverted after reload. Its phase-specific rename is left with the manual sprint setup. P00.1–P00.6 are [SCRUM-7](https://spjyotiranjan.atlassian.net/browse/SCRUM-7) through [SCRUM-12](https://spjyotiranjan.atlassian.net/browse/SCRUM-12); all six have sprint ID 35 and SCRUM-6 as parent. They are Done, so Jira's backlog view hides them and displays `0 work items` in the unstarted sprint; issue details retain sprint membership. P01 and P02 epics and sprints are created only when their respective phases start. The development tracking space is distinct from ShipSense's Release 1 Jira customer connector (P05.6).

## Complete a phase

Each issue needs evidence that its acceptance criteria passed. The phase reviewer records remaining risks and marks the epic complete only if the phase is actually complete. Sprint start, scheduling and closure are manual in ShipSense. Update `PROJECT_STATUS.md` with Jira links and proof. If any subphase remains incomplete, keep the parent in progress or review and record a follow-on decision; do not mark the phase complete based on sprint closure alone.

## Existing workspace boundary

The owner renamed the existing shared Jira space to ShipSense. Keep the `SCRUM` key and existing board; do not create a second space. Do not alter unrelated SCRUM issues or the existing active sprint. Use `shipsense` labeling and `Pxx` issue titles to distinguish ShipSense from other work in the shared space.

## Prepared P01 and P02 backlogs

P01: SCRUM-13 through SCRUM-17, one task per P01.1–P01.5. P02: SCRUM-18 through SCRUM-22, one task per P02.1–P02.5. Their phase files are the source for expected results and acceptance criteria. Add phase labels `shipsense-p01` and `shipsense-p02` to make separate Jira filters. JQL: `project = SCRUM AND labels = shipsense-p01 ORDER BY key ASC` and `project = SCRUM AND labels = shipsense-p02 ORDER BY key ASC`. All ten tasks were initially prepared in To Do without an epic or sprint. SCRUM-14 now appears in `SCRUM Sprint 1` (ID 36) without a parent epic; reconcile this before the P01 phase sprint is created. Verify current fields and move all five tasks into the phase epic and sprint when that phase starts.

## GitHub connection and merge checks

`docs/GITHUB_JIRA_INTEGRATION.md` records the issue-key convention, connected GitHub for Atlassian repository, Jira automation, and the remaining local Markdown lint hook. The Jira PR validation flow is enabled and has title, branch, and commit-key guards; its new commit guard still needs a live PR-event test. No Jira status is required by the GitHub branch ruleset yet. Keep Jira issues In Review after PR merge until the subphase acceptance evidence passes.


