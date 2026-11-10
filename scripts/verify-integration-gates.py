"""Prove maintained gates reject real drift/upstream failure and cleanly recover."""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NPM = "npm.cmd" if os.name == "nt" else "npm"


def attempt_directories() -> tuple[Path, Path]:
    # Keep ownership receipts/private state after interruption so the always
    # cleanup step can verify resources. TemporaryDirectory can delete the only
    # safe cleanup authority while external containers are still running.
    spec = importlib.util.spec_from_file_location(
        "integration_smoke", ROOT / "scripts/integration-smoke.py"
    )
    assert spec is not None and spec.loader is not None
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    base = smoke.evidence_directory() / "gate-attempts"
    return base / "failed-upstream", base / "recovered"


def cleanup_attempts(paths: tuple[Path, Path]) -> None:
    for evidence in paths:
        if evidence.exists():
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/integration-smoke.py"), "--cleanup"],
                cwd=ROOT,
                env={**os.environ, "SHIPSENSE_EVIDENCE_DIR": str(evidence)},
                check=True,
                timeout=90,
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()
    attempts = attempt_directories()
    if args.cleanup:
        cleanup_attempts(attempts)
        return
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
    try:
        for fault, evidence in zip((True, False), attempts, strict=True):
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
    finally:
        cleanup_attempts(attempts)
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
