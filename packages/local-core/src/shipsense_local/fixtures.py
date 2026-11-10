"""Inert fixture validation; no database or object storage writes."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from shipsense_local.adapters import MAX_OBJECT
from shipsense_local.config import LocalFailure, read_json

CASES = (
    "pipeline-failure",
    "probe-config-regression",
    "missing-telemetry",
    "dependency-failure",
    "injected-runbook",
    "deployment-regression",
)
Identifier = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")]
SCOPE = (
    "tenantId",
    "projectId",
    "serviceId",
    "environment",
    "provider",
    "providerObjectId",
    "providerVersion",
    "fixtureId",
)


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schemaVersion: Literal["p01-fixture-v1"]
    fixtureId: Literal[
        "pipeline-failure",
        "probe-config-regression",
        "missing-telemetry",
        "dependency-failure",
        "injected-runbook",
        "deployment-regression",
    ]
    tenantId: Identifier
    projectId: Identifier
    serviceId: Literal["product-catalog"]
    environment: Literal["local"]
    provider: Literal["synthetic"]
    providerObjectId: Identifier
    providerVersion: Identifier
    eventTime: AwareDatetime
    observedAt: AwareDatetime
    expiresAt: AwareDatetime
    freshness: Literal["fresh", "stale", "missing"]
    classification: Literal["synthetic"]
    correlationId: Identifier
    sourceRef: Annotated[str, Field(pattern=r"^payloads/[a-z-]+\.json$", max_length=100)]
    payloadSha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    expectedOutcome: Annotated[str, Field(min_length=1, max_length=240)]
    referenceRepository: Literal["https://github.com/open-telemetry/opentelemetry-demo"]
    referenceTag: Literal["3.1.0"]
    referenceRevision: Literal["dedc0178918e260823323b8d95005a8cb924b007"]

    @model_validator(mode="after")
    def valid_times(self) -> "Manifest":
        if not self.eventTime <= self.observedAt < self.expiresAt:
            raise ValueError("INVALID_FIXTURE_TIME")
        if any(
            value.utcoffset() != timedelta(0)
            for value in (self.eventTime, self.observedAt, self.expiresAt)
        ):
            raise ValueError("UTC_REQUIRED")
        if self.sourceRef != f"payloads/{self.fixtureId}.json":
            raise ValueError("INVALID_FIXTURE_SOURCE")
        return self

    def scope(self) -> dict[str, Any]:
        document = self.model_dump(mode="json")
        return {key: document[key] for key in SCOPE}

    def object_key(self) -> str:
        scope_hash = hashlib.sha256(
            json.dumps(self.scope(), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return f"synthetic/{scope_hash}/{self.payloadSha256}.json"

    def is_expired(self) -> bool:
        return self.expiresAt <= datetime.now(UTC)


def load_fixture(directory: Path, case: str) -> tuple[Manifest, bytes]:
    try:
        if case not in CASES or directory.is_symlink():
            raise LocalFailure("INVALID_FIXTURE")
        manifest = Manifest.model_validate(read_json(directory / f"{case}.json"))
        payload_path = directory / manifest.sourceRef
        if payload_path.is_symlink() or not payload_path.resolve().is_relative_to(
            directory.resolve()
        ):
            raise LocalFailure("UNSAFE_FIXTURE_PATH")
        with payload_path.open("rb") as stream:
            data = stream.read(MAX_OBJECT + 1)
        if not data or len(data) > MAX_OBJECT:
            raise LocalFailure("INVALID_FIXTURE_SIZE")
        if hashlib.sha256(data).hexdigest() != manifest.payloadSha256:
            raise LocalFailure("FIXTURE_CHECKSUM_MISMATCH")
        if not isinstance(json.loads(data), dict):
            raise LocalFailure("INVALID_FIXTURE_PAYLOAD")
        return manifest, data
    except LocalFailure:
        raise
    except Exception:
        raise LocalFailure("INVALID_OR_MISSING_FIXTURE") from None
