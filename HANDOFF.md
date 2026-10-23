# ShipSense IDE handoff

The project working directory is `D:\SDE Projects\shipsense`. Start with `ROADMAP.md`, then `Phases/README.md`, the relevant phase file, and `PROJECT_STATUS.md`. `AGENTS.md` gives repository working rules. The product source is `docs/shipsense-full-product-specification.pdf`.

The selected stack is Next.js, FastAPI, MongoDB, Cloudflare R2, LangChain, LangGraph, OpenAI API, OpenAPI/Swagger, Jira, and Azure deployment. Release 1 includes GitHub, GitHub Actions, Jira, Azure deployments, Vercel deployments, and bounded telemetry/health evidence. See accepted Decisions 0001–0002 for the delivery order and architecture. Central India is a provisional first region; P01 validates services, Atlas tier, residency, latency and an itemized cost forecast before paid provisioning.

P00 planning is complete. Work lives in ShipSense Jira space (`SCRUM`): P00 epic SCRUM-6, unstarted sprint 35, and tasks SCRUM-7–SCRUM-12. Do not start the sprint or set team allocations; those are manual. Do not create a P01 epic/sprint until P01 actually starts. No application implementation or deployed integration has been verified. P01 repository/developer foundation is the next phase.

## Jira backlog handoff (23 October 2026)

The existing Jira space was renamed from The Mentalists to **ShipSense**; its key remains `SCRUM` and its board remains `1`. P01 backlog: SCRUM-13–SCRUM-17 (P01.1–P01.5). P02 backlog: SCRUM-18–SCRUM-22 (P02.1–P02.5). Both phases remain Not started. No P01/P02 epic or sprint has been created.

All ten P01/P02 tasks (SCRUM-13–SCRUM-22) have descriptions with scope, prerequisites, acceptance criteria, and evidence requirements. At initial verification on 23 October 2026, each was To Do, phase labelled, and outside an epic and sprint. Jira now shows SCRUM-14 in `SCRUM Sprint 1` (ID 36), without a parent epic; this change was not made as part of the integration work. Recheck current sprint membership before starting a phase, and leave owners, estimates, dates, and sprint start to the team.

## GitHub and Jira integration (23 October 2026)

`docs/GITHUB_JIRA_INTEGRATION.md` records the development-key rule and verification steps. Jira shows GitHub for Atlassian connected to `spjyotiranjan`; a temporary PR appeared in its Development list, and Atlassian's bot made a bracketed key clickable in a GitHub comment. The temporary PR and branch were removed after this test. The Jira flow `ShipSense: PR created -> In Review` is enabled for future qualifying PRs, with no trigger run yet. The GitHub `Jira issue verified` job needs repository secrets and a required-check ruleset before it can gate merges. Tracked Git hooks provide Markdown lint and commit-subject validation after `git config core.hooksPath .githooks` in each clone.

