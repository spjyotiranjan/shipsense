"""Prove real quality gates reject independent probes and recover after removal.

Run serially in an exclusively held checkout. Probes are restored in finally;
the synthetic public AWS example is never printed or sent to a provider.
"""

import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
NPM = "npm.cmd" if os.name == "nt" else "npm"


def check(target: str, fails_with: str = "", redacted: str = "") -> None:
    result = subprocess.run(
        [NPM, "run", target], cwd=ROOT, capture_output=True, timeout=180, check=False
    )
    output = result.stdout.decode("utf-8", errors="replace") + result.stderr.decode(
        "utf-8", errors="replace"
    )
    if redacted and redacted in output:
        raise RuntimeError("secret output was not redacted")
    if fails_with:
        if result.returncode == 0 or fails_with not in output:
            raise RuntimeError(f"{target}: expected rejection rule was absent")
    elif result.returncode:
        raise RuntimeError(f"{target}: clean recovery failed")


@contextmanager
def probe(relative: str, content: str, append: bool = False) -> Iterator[None]:
    path = ROOT / relative
    original = path.read_bytes() if path.exists() else None
    if original is not None and not append:
        raise RuntimeError("probe path already exists")
    try:
        path.write_bytes((original or b"") + content.encode("utf-8"))
        yield
    finally:
        if original is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(original)


def main() -> None:
    check("quality")
    # Public AWS documentation test vector; never a provisioned credential.
    synthetic = "AKIA" + "IOSFODNN7EXAMPLE"
    cases = [
        (
            "format:check",
            "apps/web/src/quality_gate_probe.ts",
            "const qualityProbe={label:'synthetic'}; void qualityProbe;\n",
            "quality_gate_probe.ts",
        ),
        ("lint", "apps/web/src/quality_gate_probe.ts", "debugger;\n", "no-debugger"),
        (
            "typecheck",
            "apps/web/src/quality_gate_probe.ts",
            'const qualityProbe: number = "synthetic";\nvoid qualityProbe;\n',
            "not assignable",
        ),
        (
            "secrets:check",
            "tests/fixtures/quality_gate_probe.txt",
            "AWS_ACCESS_KEY_ID=" + synthetic + "\n",
            "AWS Access Key",
        ),
        ("contracts:check", "packages/contracts/openapi.json", "\n", "CONTRACT_DRIFT"),
        ("contracts:check", "packages/contracts/src/generated.ts", "\n", "CONTRACT_DRIFT"),
    ]
    for target, relative, content, rule in cases:
        with probe(relative, content, append=target == "contracts:check"):
            check(target, rule, synthetic)
            check("quality", rule, synthetic)
        check(target)
        print(f"Verified rejection and recovery: {target} ({rule})", flush=True)
    check("quality")
    print("All independent quality-gate probes recovered.")


if __name__ == "__main__":
    main()
