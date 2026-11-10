"""Server-only hosted configuration and read-only infrastructure probes.

No provisioning, seed, migrations, credential discovery or local fallback.
"""

import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, unquote, urlsplit

from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError, field_validator
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from shipsense_local.adapters import BoundedObjects, private_s3
from shipsense_local.config import LocalFailure

from shipsense_api.readiness_runtime import DependencyReadiness


class HostedSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, hide_input_in_errors=True)
    mongodb_uri: SecretStr
    mongodb_database: str
    r2_endpoint: str
    r2_bucket: str
    r2_access_key_id: SecretStr
    r2_secret_access_key: SecretStr

    @field_validator("mongodb_uri")
    @classmethod
    def mongo_transport(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if not 1 <= len(raw) <= 4096 or any(c.isspace() or c in "<>\\" for c in raw):
            raise ValueError("INVALID_HOSTED_CONFIG")
        uri = urlsplit(raw)
        if (
            uri.scheme not in ("mongodb", "mongodb+srv")
            or not uri.username
            or not uri.password
            or uri.fragment
            or not uri.hostname
            or "replace" in raw.lower()
        ):
            raise ValueError("INVALID_HOSTED_CONFIG")
        # Do not allow URI options to select files, weaken TLS, redirect the
        # resolver or override the adapter's resource and timeout bounds.
        allowed = {"authsource", "replicaset", "retrywrites", "w", "appname", "tls", "ssl"}
        options = parse_qsl(uri.query, keep_blank_values=True, strict_parsing=True)
        keys = [key.lower() for key, _ in options]
        if len(keys) != len(set(keys)) or any(key not in allowed for key in keys):
            raise ValueError("INVALID_HOSTED_CONFIG")
        for key, item in options:
            if key.lower() in {"tls", "ssl"} and item.lower() != "true":
                raise ValueError("INVALID_HOSTED_CONFIG")
        # Hosted standard strings can have multiple DNS seeds. No sockets,
        # literal IPs or localhost targets. Integration uses the same hosted loader.
        hosts = uri.netloc.rsplit("@", 1)[-1].split(",")
        if uri.scheme == "mongodb+srv" and (len(hosts) != 1 or ":" in hosts[0]):
            raise ValueError("INVALID_HOSTED_CONFIG")
        for seed in hosts:
            parts = seed.split(":")
            host = parts[0].lower()
            if (
                len(parts) > 2
                or not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?", host)
                or "." not in host
                or host.endswith((".localhost", ".local"))
                or re.fullmatch(r"[0-9.]+", host)
                or (len(parts) == 2 and (not parts[1].isdigit() or not 1 <= int(parts[1]) <= 65535))
            ):
                raise ValueError("INVALID_HOSTED_CONFIG")
        if uri.path not in ("", "/") and not re.fullmatch(
            r"/[A-Za-z][A-Za-z0-9_-]{0,62}", uri.path
        ):
            raise ValueError("INVALID_HOSTED_CONFIG")
        for credential in (uri.username, uri.password):
            decoded = unquote(credential)
            if not decoded or any(ord(c) < 32 for c in decoded):
                raise ValueError("INVALID_HOSTED_CONFIG")
        return value

    @field_validator("mongodb_database")
    @classmethod
    def database_name(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,62}", value) or value.lower() in {
            "admin",
            "config",
            "local",
        }:
            raise ValueError("INVALID_HOSTED_CONFIG")
        return value

    @field_validator("r2_endpoint")
    @classmethod
    def r2_transport(cls, value: str) -> str:
        if not re.fullmatch(
            r"https://[a-f0-9]{32}\.r2(?:\.eu|\.fedramp)?\.cloudflarestorage\.com", value
        ):
            raise ValueError("INVALID_HOSTED_CONFIG")
        return value

    @field_validator("r2_bucket")
    @classmethod
    def bucket_name(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", value) or "replace" in value:
            raise ValueError("INVALID_HOSTED_CONFIG")
        return value

    @field_validator("r2_access_key_id", "r2_secret_access_key")
    @classmethod
    def credential(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if (
            not 16 <= len(raw) <= 256
            or not raw.isascii()
            or any(c.isspace() or c in "<>" for c in raw)
            or "replace" in raw.lower()
        ):
            raise ValueError("INVALID_HOSTED_CONFIG")
        return value

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> "HostedSettings":
        try:
            return cls.model_validate(
                {
                    field: environment.get("SHIPSENSE_" + field.upper(), "")
                    for field in cls.model_fields
                }
            )
        except ValidationError, ValueError:
            raise LocalFailure("HOSTED_CONFIG_INVALID") from None


class HostedClients:
    """Lazy pooled Mongo and private R2 clients; readiness performs only reads."""

    def __init__(self, settings: HostedSettings) -> None:
        self.mongo: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
            settings.mongodb_uri.get_secret_value(),
            tls=True,
            tlsAllowInvalidCertificates=False,
            tlsAllowInvalidHostnames=False,
            server_api=ServerApi("1"),
            connect=False,
            serverSelectionTimeoutMS=800,
            connectTimeoutMS=500,
            socketTimeoutMS=800,
            waitQueueTimeoutMS=350,
            timeoutMS=900,
            maxPoolSize=4,
            minPoolSize=0,
            maxConnecting=2,
        )
        self.database = self.mongo[settings.mongodb_database]
        self.objects: BoundedObjects

    async def mongo_probe(self) -> bool:
        try:
            # Read authorization on the configured database, without enumerating
            # customer records or counting denied data. Never ping as auth proof.
            await self.database.fixtures.find_one(
                {
                    "tenantId": "synthetic-health",
                    "projectId": "synthetic-local",
                    "serviceId": "foundation",
                    "environment": "local",
                    "provider": "synthetic",
                    "providerObjectId": "hosted-probe",
                    "providerVersion": "p01",
                },
                {"_id": 1},
            )
            return True
        except Exception:
            return False

    async def close(self) -> None:
        try:
            if hasattr(self, "objects"):
                await self.objects.close()
        finally:
            await self.mongo.close()


class HostedReadiness(DependencyReadiness):
    @classmethod
    async def from_environment(cls, environment: Mapping[str, str]) -> "HostedReadiness":
        settings = HostedSettings.from_environment(environment)
        clients = HostedClients(settings)
        try:
            clients.objects = BoundedObjects(
                settings.r2_bucket,
                private_s3(
                    settings.r2_endpoint,
                    "auto",
                    settings.r2_access_key_id.get_secret_value(),
                    settings.r2_secret_access_key.get_secret_value(),
                ),
            )
            return cls(clients)
        except BaseException:
            await clients.close()
            raise
