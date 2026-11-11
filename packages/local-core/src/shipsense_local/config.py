"""Fail closed on anything other than the explicitly owned synthetic profile."""

import json
import os
from pathlib import Path
from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

PROJECT: Final = "shipsense-local-p01"
DATABASE: Final = "shipsense_fixture_p01"
BUCKET: Final = "shipsense-fixtures"
ROOT = Path(__file__).resolve().parents[4]


class LocalFailure(RuntimeError):
    """Only fixed safe codes cross the CLI/diagnostic boundary."""


class LocalSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    profile: Literal["local"]
    project: Literal["shipsense-local-p01"]
    repository: str
    owner: Annotated[str, Field(pattern=r"^[a-f0-9]{32}$")]
    mongo_host: Literal["127.0.0.1"]
    mongo_port: Literal[37017]
    database: Literal["shipsense_fixture_p01"]
    mongo_user: Literal["shipsense_fixture"]
    mongo_password: SecretStr
    s3_endpoint: Literal["http://127.0.0.1:38333"]
    bucket: Literal["shipsense-fixtures"]
    access_key: SecretStr
    secret_key: SecretStr

    @field_validator("mongo_password", "access_key", "secret_key")
    @classmethod
    def bounded_secret(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if not 32 <= len(raw) <= 128 or not raw.isascii() or not raw.isalnum():
            raise ValueError("INVALID_LOCAL_SECRET")
        return value


def local_profile() -> None:
    if os.environ.get("SHIPSENSE_PROFILE", "local") != "local":
        raise LocalFailure("LOCAL_PROFILE_REQUIRED")


def state_path(path: Path) -> Path:
    """No linked state directories or credentials inside the product tree."""
    local_profile()
    absolute = path.absolute()
    if any(part.is_symlink() or part.is_junction() for part in (absolute, *absolute.parents)):
        raise LocalFailure("UNSAFE_STATE_DIRECTORY")
    resolved = absolute.resolve()
    if resolved == ROOT or resolved.is_relative_to(ROOT) or resolved == resolved.parent:
        raise LocalFailure("UNSAFE_STATE_DIRECTORY")
    return resolved


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


def identity(settings: LocalSettings) -> dict[str, object]:
    return {
        "identities": [
            {
                "name": "shipsense-fixture",
                "credentials": [
                    {
                        "accessKey": settings.access_key.get_secret_value(),
                        "secretKey": settings.secret_key.get_secret_value(),
                    }
                ],
                "actions": [f"{action}:{BUCKET}" for action in ("Read", "Write", "List")],
            }
        ]
    }


def load_settings(path: Path) -> LocalSettings:
    directory = state_path(path)
    try:
        settings = LocalSettings.model_validate(read_json(directory / "local.json"))
        if settings.repository != str(ROOT.resolve()):
            raise LocalFailure("UNOWNED_LOCAL_TARGET")
        if read_json(directory / "s3.json") != identity(settings):
            raise LocalFailure("PRIVATE_S3_CONFIG_REQUIRED")
        if read_json(directory / "mongo-app.json") != {
            "user": settings.mongo_user,
            "pwd": settings.mongo_password.get_secret_value(),
        }:
            raise LocalFailure("LOCAL_CONFIG_MISMATCH")
        root_password = directory / "mongo-root.txt"
        if root_password.is_symlink() or not root_password.is_file():
            raise LocalFailure("LOCAL_CONFIG_MISSING")
        value = root_password.read_text().strip()
        if len(value) != 64 or not value.isalnum():
            raise LocalFailure("LOCAL_CONFIG_INVALID")
        return settings
    except LocalFailure:
        raise
    except Exception:
        raise LocalFailure("LOCAL_CONFIG_INVALID") from None
