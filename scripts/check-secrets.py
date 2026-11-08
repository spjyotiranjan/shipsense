"""Offline secret gate: findings and scanner errors fail, values never print."""

import logging
import os
import re
import subprocess
from pathlib import Path

from detect_secrets.core.log import log
from detect_secrets.core.scan import scan_file
from detect_secrets.settings import default_settings


class ScannerError(RuntimeError):
    pass


class FailClosedHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # The library sometimes logs and returns instead of raising. Never print
        # its diagnostic, which can contain sensitive input or exception text.
        raise ScannerError("scanner diagnostic")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    log.handlers = [FailClosedHandler()]
    log.propagate = False
    log.setLevel(logging.WARNING)
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            check=True,
            capture_output=True,
        )
        paths = sorted(set(os.fsdecode(result.stdout).split("\0")) - {""})
        findings = 0
        scanned = 0
        with default_settings() as settings:
            # No network verification, inline suppressions or file-wide source
            # exclusions, including for dependency locks.
            settings.disable_filters(
                "detect_secrets.filters.common.is_ignored_due_to_verification_policies",
                "detect_secrets.filters.allowlist.is_line_allowlisted",
                "detect_secrets.filters.common.is_invalid_file",
                "detect_secrets.filters.heuristic.is_swagger_file",
                "detect_secrets.filters.heuristic.is_non_text_file",
                "detect_secrets.filters.heuristic.is_lock_file",
            )
            for filename in paths:
                path = root / filename
                if not path.exists():
                    # A tracked deletion is no longer an input.
                    continue
                if (
                    path.is_symlink()
                    or not path.is_file()
                    or not path.resolve().is_relative_to(root)
                ):
                    raise ScannerError("unsupported input")
                if path.stat().st_size > 10_000_000:
                    raise ScannerError("input exceeds scan bound")
                content = path.read_bytes()
                # Known binary product/document assets only. Null bytes in
                # source/config fail rather than bypassing the gate.
                if (path.suffix == ".pdf" and content.startswith(b"%PDF-")) or (
                    path.suffix == ".ico" and content.startswith(b"\x00\x00\x01\x00")
                ):
                    continue
                if b"\0" in content:
                    raise ScannerError("binary source input")
                lines = content.decode("utf-8-sig").splitlines()
                for secret in scan_file(filename):
                    # npm integrity digests are public package checksums, not
                    # credentials. Exempt only an entire integrity field with
                    # the expected algorithm/length, and only entropy findings.
                    if (
                        filename == "package-lock.json"
                        and secret.type == "Base64 High Entropy String"
                        and re.fullmatch(
                            r'\s*"integrity": "sha512-[A-Za-z0-9+/]{86}==",?\s*',
                            lines[secret.line_number - 1],
                        )
                    ):
                        continue
                    print(
                        f"SECRET_FINDING {filename}:{secret.line_number} {secret.type} [REDACTED]"
                    )
                    findings += 1
                scanned += 1
        if findings:
            return 1
        print(f"Offline secret scan passed ({scanned} files).")
        return 0
    except Exception:
        print("SECRET_SCANNER_ERROR [details redacted]")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
