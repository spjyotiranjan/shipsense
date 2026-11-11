"""Prove contract and built-web gates reject drift/failure and recover without services."""

import importlib.util
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NPM = "npm.cmd" if os.name == "nt" else "npm"


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "integration_smoke", ROOT / "scripts/integration-smoke.py"
    )
    assert spec is not None and spec.loader is not None
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    directory = smoke.evidence_directory()
    path = ROOT / "packages/contracts/openapi.json"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\n")
        result = subprocess.run(
            [NPM, "run", "contracts:check"], cwd=ROOT, capture_output=True, timeout=120
        )
        if result.returncode == 0 or b"CONTRACT_DRIFT" not in result.stdout:
            raise RuntimeError("CONTRACT_REJECTION_NOT_PROVED")
    finally:
        path.write_bytes(original)
    subprocess.run([NPM, "run", "contracts:check"], cwd=ROOT, check=True, timeout=120)
    try:
        smoke.smoke(directory, hosted=False, fail_upstream=True)
    except smoke.LocalFailure as error:
        if str(error) != "UPSTREAM_SUCCESS_GATE_REJECTED":
            raise RuntimeError("UPSTREAM_REJECTION_NOT_PROVED") from None
    else:
        raise RuntimeError("UPSTREAM_REJECTION_NOT_PROVED")
    smoke.smoke(smoke.evidence_directory(), hosted=False, fail_upstream=False)
    (directory / "gate-proof.json").write_text(
        json.dumps(
            {
                "contractDriftRejected": True,
                "contractRestored": True,
                "upstreamFailureRejected": True,
                "freshRecoveryPassed": True,
                "hostedAccessVerified": False,
            }
        )
        + "\n"
    )
    print("Contract drift and stopped API rejected; credential-free browser recovered.", flush=True)


if __name__ == "__main__":
    main()
