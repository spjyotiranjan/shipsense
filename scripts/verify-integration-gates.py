"""Prove maintained gates reject real drift/upstream failure and cleanly recover."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NPM = "npm.cmd" if os.name == "nt" else "npm"


def main() -> None:
    path = ROOT / "packages/contracts/openapi.json"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\n")
        result = subprocess.run(
            [NPM, "run", "contracts:check"], cwd=ROOT, capture_output=True, timeout=120
        )
        if result.returncode == 0 or b"CONTRACT_DRIFT" not in result.stdout:
            raise RuntimeError("CONTRACT_REJECTION_NOT_PROVED")
        print("Actual contract gate rejected seeded byte drift.", flush=True)
    finally:
        path.write_bytes(original)
    subprocess.run([NPM, "run", "contracts:check"], cwd=ROOT, check=True, timeout=120)
    with tempfile.TemporaryDirectory(prefix="shipsense-gate-proof-") as temporary:
        base = Path(temporary)
        for fault in (True, False):
            evidence = base / ("failed-upstream" if fault else "recovered")
            env = {**os.environ, "SHIPSENSE_EVIDENCE_DIR": str(evidence)}
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/integration-smoke.py"),
                    *(["--fail-upstream"] if fault else []),
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                timeout=600,
            )
            if fault:
                if result.returncode != 2 or json.loads(
                    (evidence / "failure.json").read_text()
                ) != {"error": "UPSTREAM_SUCCESS_GATE_REJECTED"}:
                    raise RuntimeError("UPSTREAM_REJECTION_NOT_PROVED")
            elif result.returncode:
                raise RuntimeError("SMOKE_RECOVERY_FAILED")
            if json.loads((evidence / "cleanup.json").read_text())["ciResourcesRemaining"] != 0:
                raise RuntimeError("FAILURE_CLEANUP_NOT_PROVED")
            print(
                "Actual built-web smoke rejected stopped upstream and cleaned up."
                if fault
                else "Fresh smoke recovered and cleaned up.",
                flush=True,
            )
    output = os.environ.get("SHIPSENSE_EVIDENCE_DIR")
    if output:
        directory = Path(output)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "gate-proof.json").write_text(
            json.dumps(
                {
                    "contractDriftRejected": True,
                    "contractRestored": True,
                    "upstreamFailureRejected": True,
                    "freshRecoveryPassed": True,
                    "failureCleanupPassed": True,
                }
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
