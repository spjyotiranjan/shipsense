# Local foundation setup

Use the supplied primary checkout. Required versions: Node 26.7.0, npm 11.19.0, Python 3.14.7 and uv 0.12.21. Runtime/version files and root locks define initial reproducibility. Do not substitute floating versions. Package registries are required for a fresh install; no cloud or provider credentials are required.

From the repository root:

```powershell
git config core.hooksPath .githooks
npm ci
uv sync --frozen --all-packages --all-groups
npm run contracts:generate
npm run contracts:check
npm run test:foundation
python scripts/validate-foundation.py
uv build --package shipsense-api
uv build --package shipsense-worker
uv run --frozen --package shipsense-worker shipsense-worker
npm run typecheck:web
npm run build:web
```

Run the API: `uv run --frozen --package shipsense-api uvicorn shipsense_api.main:create_app --factory --host 127.0.0.1 --port 8000`. In another terminal run the web: `npm run start --workspace apps/web -- --hostname 127.0.0.1`. Visit `http://127.0.0.1:3000`, API `/foundation`, `/docs` and `/openapi.json` on port 8000. Stop each foreground process with Ctrl+C. The static web is independent of the API in P01.1.

No environment file is needed. `SHIPSENSE_PROFILE` accepts only `local`; other profiles fail closed. Test a missing fixture with `python scripts/validate-foundation.py --fixture tests/fixtures/absent.json` (expected exit 2, `FIXTURE_MISSING`). Use `--config infra/absent.json` for `CONFIG_MISSING`. Errors contain codes rather than supplied file contents.

P01.2 adds full format/lint/type/secret and CI quality enforcement. P01.3 selects and starts local services. P01.4 adds health/version and real web-to-API diagnostics. P01.5 proves clean-checkout CI. Those outcomes are not established by this skeleton.
