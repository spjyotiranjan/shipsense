"""Shared bounded inert-fixture input and safe failure codes; no service provisioning."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


class LocalFailure(RuntimeError):
    """Only fixed safe codes cross diagnostic boundaries."""


def local_profile() -> None:
    if os.environ.get("SHIPSENSE_PROFILE", "local") != "local":
        raise LocalFailure("LOCAL_PROFILE_REQUIRED")


def read_json(path: Path, limit: int = 16384) -> object:
    if path.is_symlink() or not path.is_file():
        raise LocalFailure("LOCAL_CONFIG_MISSING")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise LocalFailure("LOCAL_INPUT_TOO_LARGE")

    def unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
        values: dict[str, object] = {}
        for key, value in pairs:
            if key in values:
                raise LocalFailure("AMBIGUOUS_LOCAL_INPUT")
            values[key] = value
        return values

    return json.loads(raw, object_pairs_hook=unique_fields)
