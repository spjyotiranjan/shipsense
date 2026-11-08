# Decision 0006 — Local quality toolchain

**Date:** 9 November 2026
**Status:** Accepted starting choices; compatibility and quality proof remain delivery gates.
**Decision owner:** Patrick Jane, within delegated technical authority.

## Decision

For P01.2 use Prettier 3.9.10, ESLint 9.39.5, eslint-config-next 16.4.5, typescript-eslint 8.72.1, Ruff 0.17.4, mypy 2.4.1 and detect-secrets 1.5.0 as pinned development tools. Preserve Decision 0005 runtime pins and one frozen lock per language. Apply formatting, lint and typing to maintained web/API/worker code and scripts. Check canonical OpenAPI and generated TypeScript drift by byte comparison separately from typechecking.

Secret scanning must fail closed on findings and scanner errors, redact matched values, cover tracked and nonignored untracked relevant inputs including .env.example, and disable network credential verification. Do not accept blanket baselines or broad source exclusions. Synthetic failures and restored success must prove the real quality gates.

Minimal quality CI uses read-only permissions, no provider secrets, immutable action references, bounded execution and the same documented frozen-install/local quality commands. Jira continues to own development-key validation under Decision 0003. Full build/smoke CI remains P01.5.

## Rationale and limits

These tools implement the accepted phase quality requirements without changing the product stack. Registry metadata reported by the author is preliminary evidence; exact availability and runtime compatibility must be demonstrated by frozen installs and affected build/import/startup, contract and independent failure/recovery checks before delivery. A failed pin requires a concrete replacement proposal rather than a silent change. Local proof does not satisfy the required seeded CI failure proof. No cloud provisioning, spending, production runtime, issuer or emulator selection is authorized.

## Compatibility correction — 9 November 2026

ESLint 9.39.5 supersedes the initial ESLint 10.14.0 starting choice. The resolved import, JSX accessibility and React plugins exclude ESLint 10; their peer ranges and typescript-eslint 8.72.1 accept ESLint 9. Preserve the other six development pins and Decision 0005 runtimes. Frozen installation, a valid dependency tree and real lint/build/contract failure-and-recovery checks remain required; peer metadata alone is not compatibility proof. Do not bypass peer checks.

## Sources

- Accepted P01 technical web/backend plans and Decisions 0001–0005.
- Tool proposal: PAT-104 comment 3cdeea68-7c07-4e45-b09a-ce27c957f40a.
- Exact npm registry version endpoints for prettier/3.9.10, eslint/9.39.5, eslint-config-next/16.4.5 and typescript-eslint/8.72.1; PyPI version endpoints for ruff/0.17.4, mypy/2.4.1 and detect-secrets/1.5.0.
- Compatibility replacement proposal: PAT-104 comment de501c6b-b2cf-4e98-a2d9-da83baf1bce5; accepted by Patrick on 9 November 2026, based on the recorded dependency-tree failure and replacement metadata.

## Minimal quality CI action pins - 9 November 2026

Use these immutable upstream references for the P01.2 quality workflow:

- actions/checkout v4.2.2: 11bd71901bbe5b1630ceea73d27597364c9af683.
- actions/setup-node v4.4.0: 49933ea5288caeca8642d1e84afbd3f7d6820020.
- actions/setup-python v5.6.0: a26af69be951a213d495a4c3e4e4022e16d87065.

Retain Decision 0005 runtime versions; install uv==0.12.21 using Python pip, reproduce both frozen dependency installs, and run the same documented npm run quality command. Limit workflow permissions to contents: read, disable persisted checkout credentials, provide no provider secrets, and bound execution time. Do not execute untrusted pull-request code through pull_request_target. These are starting workflow selections; successful setup and independent seeded CI failures followed by recovery remain required proof.

Sources: upstream releases https://github.com/actions/checkout/releases/tag/v4.2.2, https://github.com/actions/setup-node/releases/tag/v4.4.0 and https://github.com/actions/setup-python/releases/tag/v5.6.0; the release commit links match the full SHAs above.
