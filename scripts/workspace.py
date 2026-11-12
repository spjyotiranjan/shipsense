"""Maintained local/CI commands; output and distributions stay outside the checkout."""

import argparse
import os
import platform
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NPM = "npm.cmd" if os.name == "nt" else "npm"


def run(*command: str, timeout: int = 600) -> None:
    subprocess.run(command, cwd=ROOT, check=True, timeout=timeout)


def version(*command: str) -> str:
    return subprocess.check_output(command, cwd=ROOT, text=True, timeout=15).strip()


def bootstrap() -> None:
    expected = {
        "node": (version("node", "--version"), "v26.7.0"),
        "npm": (version(NPM, "--version"), "11.19.0"),
        "python": (platform.python_version(), "3.14.7"),
        "uv": (" ".join(version("uv", "--version").split()[:2]), "uv 0.12.21"),
    }
    if any(actual != pin for actual, pin in expected.values()):
        raise RuntimeError("PINNED_TOOL_VERSION_REQUIRED")
    run(NPM, "ci")
    run("uv", "lock", "--check")
    run("uv", "sync", "--frozen", "--all-packages", "--all-groups")
    print("Frozen workspace installed with exact pinned tools.", flush=True)


def units() -> None:
    for directory, pattern in (
        ("services/api/tests", "test_foundation.py"),
        ("services/api/tests", "test_diagnostics.py"),
        ("services/api/tests", "test_hosted_lifespan.py"),
        ("services/api/tests", "test_hosted.py"),
        ("services/api/tests", "test_identity_contract.py"),
        ("packages/local-core/tests", "test_unit.py"),
        ("packages/domain/tests", "test_identity.py"),
        ("scripts/tests", "test_integration_smoke.py"),
    ):
        run(
            "uv",
            "run",
            "--frozen",
            "--package",
            "shipsense-api",
            "python",
            "-m",
            "unittest",
            "discover",
            "-s",
            directory,
            "-p",
            pattern,
            "-v",
        )
    run(NPM, "run", "test:web")
    run(NPM, "run", "queue:smoke")
    run("uv", "run", "--frozen", "python", "scripts/validate-foundation.py")


def build() -> None:
    run(NPM, "run", "build:web")
    with tempfile.TemporaryDirectory(prefix="shipsense-distributions-") as directory:
        for package in ("shipsense-local", "shipsense-domain", "shipsense-api", "shipsense-worker"):
            run("uv", "build", "--package", package, "--out-dir", directory)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("bootstrap", "unit", "build", "verify"))
    args = parser.parse_args()
    if args.command == "bootstrap":
        bootstrap()
    elif args.command == "unit":
        units()
    elif args.command == "build":
        build()
    else:
        run(NPM, "run", "quality")
        units()
        build()
        run(NPM, "run", "test:smoke", timeout=900)


if __name__ == "__main__":
    main()
