# Developer setup

Use the pinned Node, npm, Python and uv versions in `.node-version`, `.python-version`, `package.json` and `pyproject.toml`.

```powershell
npm run bootstrap
Copy-Item .env.example .env.local
```

Keep `SHIPSENSE_PROFILE=local`; set a MongoDB base name (the target is exactly `{base}-local`, at most 63 bytes). Fill the MongoDB/R2 placeholders privately with existing non-production hosted credentials. `.env.local` is ignored. Keep the bucket private and use credentials restricted to the intended database and bucket. No database or storage service is installed or started by this repository.

Start the API with server-only settings:

```powershell
uv run --env-file .env.local --frozen --package shipsense-api uvicorn shipsense_api.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

Start Next.js in another terminal with only `SHIPSENSE_API_ORIGIN=http://127.0.0.1:8000` in its environment:

```powershell
npm run dev --workspace apps/web
```

See [API configuration](../services/api/README.md) for the setting contract. Empty/invalid configuration leaves readiness at 503; liveness, version, OpenAPI and web diagnostics remain available. The diagnostic UI's Connected state means API reachability.

## Quality checks

```powershell
npm run check
npm run test:unit
npm run build
```

Frozen installs, generated-contract drift, formatting, lint, strict types and offline secret checks are required. Build output and disposable captures/logs stay outside the repository (Next.js cache is ignored). Preserve the tracked Markdown hook with `git config core.hooksPath .githooks`.

## Clean integration commands

```powershell
npm run test:smoke
uv run --frozen --package shipsense-api python scripts/verify-integration-gates.py
```

These credential-free checks start only owned API/web/browser processes on loopback ports 8000/3000. They prove safe missing/invalid configuration, matching web/API version, actual stopped-API failure, retry, browser focus and recovery. They do not claim live hosted access. An already installed compatible Chrome/Chromium is required; optionally set `SHIPSENSE_CHROME`. Occupied ports fail without stopping another process. Evidence uses a unique private external temporary directory; optionally set an absolute external `SHIPSENSE_EVIDENCE_DIR`.

The existing real-connection integration test is optional and is not a separate release gate. To exercise its supported MongoDB/R2 coverage, stop your development API/web first and load private non-production settings explicitly:

```powershell
uv run --env-file .env.local --frozen --package shipsense-api python scripts/integration-smoke.py --hosted
```

Or run `npm run test:integration` with the server settings already loaded into the environment. This uses the same hosted settings as application startup. It verifies a scoped MongoDB read, authenticated R2 HeadBucket, anonymous/wrong-key authentication rejection using ListObjectsV2 with MaxKeys=0 (no object names or contents), actual readiness 200 and API/web/browser stop/retry/recovery. It performs no writes, seed, migration, provisioning or provider-service restart. Authentication rejection is not a full bucket-policy audit. Missing credentials, TLS/access failures or a failed assertion exit nonzero; nothing skips to a live success.

Pull-request/push [Integration CI](../.github/workflows/integration.yml) runs the credential-free build/contracts/unit/browser checks without hosted secrets. There is no manual hosted-verification job, protected hosted-result or environment-approval acceptance gate. Keep provider settings private and isolated from untrusted PR execution. Unsupported or unexercised provider coverage remains explicit; mocked SDK checks and credential-free smoke do not establish live compatibility.
