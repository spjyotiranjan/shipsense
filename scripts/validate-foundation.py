"""Validate credential-free foundation inputs without side effects."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_KEYS = {
    "schemaVersion",
    "fixtureId",
    "tenantId",
    "projectId",
    "serviceId",
    "environment",
    "provider",
    "providerObjectId",
    "providerVersion",
    "eventTime",
    "observedAt",
    "freshness",
    "expectedOutcome",
}


def read_bounded(path: Path, missing_code: str) -> dict[str, object]:
    try:
        with path.open("rb") as stream:
            raw = stream.read(8193)
        if len(raw) > 8192:
            raise ValueError("INPUT_TOO_LARGE")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("INVALID_INPUT")
        return cast(dict[str, object], data)
    except FileNotFoundError:
        raise ValueError(missing_code) from None
    except OSError, UnicodeError, json.JSONDecodeError:
        raise ValueError("INVALID_INPUT") from None


def validate(fixture: Path, config: Path) -> None:
    data = read_bounded(fixture, "FIXTURE_MISSING")
    if set(data) != FIXTURE_KEYS or any(
        not isinstance(value, str) or not 1 <= len(value) <= 80 for value in data.values()
    ):
        raise ValueError("INVALID_FIXTURE")
    required = {
        "schemaVersion": "foundation-v1",
        "environment": "local",
        "provider": "synthetic",
        "freshness": "missing",
        "expectedOutcome": "no-effects",
    }
    if any(data[key] != value for key, value in required.items()):
        raise ValueError("INVALID_FIXTURE")
    for key in ("eventTime", "observedAt"):
        value = data[key]
        if not isinstance(value, str) or not value.endswith("Z"):
            raise ValueError("INVALID_FIXTURE")
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise ValueError("INVALID_FIXTURE") from None
    local = read_bounded(config, "CONFIG_MISSING")
    expected = {
        "profile": "local",
        "bindHost": "127.0.0.1",
        "apiPort": 8000,
        "webPort": 3000,
        "effectsEnabled": False,
    }
    if local != expected or any(
        type(local[key]) is not type(value) for key, value in expected.items()
    ):
        raise ValueError("INVALID_LOCAL_CONFIG")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=ROOT / "tests/fixtures/foundation.json")
    parser.add_argument("--config", type=Path, default=ROOT / "infra/local.example.json")
    args = parser.parse_args()
    try:
        validate(args.fixture, args.config)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    print("Foundation inputs valid; no effects performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
