"""Owned Compose lifecycle. Never reset an arbitrary endpoint or Docker project."""

import csv
import json
import os
import secrets
import socket
import subprocess
from pathlib import Path
from typing import Any

from pydantic import SecretStr

from shipsense_local.config import (
    BUCKET,
    DATABASE,
    PROJECT,
    ROOT,
    LocalFailure,
    LocalSettings,
    identity,
    load_settings,
    state_path,
)

COMPOSE = ROOT / "infra/local/compose.yaml"


def private_write(path: Path, value: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)


def initialize(path: Path) -> LocalSettings:
    directory = state_path(path)
    if directory.exists():
        return load_settings(directory)
    directory.mkdir(parents=True, mode=0o700)
    if os.name == "nt":
        # Do not inherit broad temp/parent ACLs onto generated credential files.
        account = subprocess.run(
            ["whoami", "/user", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if account.returncode:
            raise LocalFailure("PRIVATE_STATE_PERMISSIONS_FAILED")
        sid = next(csv.reader(account.stdout.splitlines()))[1]
        if not sid.startswith("S-1-"):
            raise LocalFailure("PRIVATE_STATE_PERMISSIONS_FAILED")
        result = subprocess.run(
            [
                "icacls",
                str(directory),
                "/inheritance:r",
                "/grant:r",
                f"*{sid}:(OI)(CI)F",
            ],
            capture_output=True,
            timeout=10,
        )
        if result.returncode:
            raise LocalFailure("PRIVATE_STATE_PERMISSIONS_FAILED")
    settings = LocalSettings(
        profile="local",
        project=PROJECT,
        repository=str(ROOT.resolve()),
        owner=secrets.token_hex(16),
        mongo_host="127.0.0.1",
        mongo_port=37017,
        database=DATABASE,
        mongo_user="shipsense_fixture",
        mongo_password=SecretStr(secrets.token_hex(32)),
        access_key=SecretStr(secrets.token_hex(16)),
        secret_key=SecretStr(secrets.token_hex(32)),
        s3_endpoint="http://127.0.0.1:38333",
        bucket=BUCKET,
    )
    values = settings.model_dump(mode="json")
    for key in ("mongo_password", "access_key", "secret_key"):
        values[key] = getattr(settings, key).get_secret_value()
    private_write(directory / "local.json", json.dumps(values) + "\n")
    private_write(directory / "mongo-root.txt", secrets.token_hex(32) + "\n")
    private_write(
        directory / "mongo-app.json",
        json.dumps(
            {
                "user": settings.mongo_user,
                "pwd": settings.mongo_password.get_secret_value(),
            }
        )
        + "\n",
    )
    private_write(directory / "s3.json", json.dumps(identity(settings)) + "\n")
    return load_settings(directory)


class LocalStack:
    def __init__(self, directory: Path, settings: LocalSettings) -> None:
        self.directory = state_path(directory)
        self.settings = settings
        self.env = os.environ.copy()
        # Explicit files/project; inherited Compose options must not expand scope.
        for key in list(self.env):
            if key.startswith("COMPOSE_") or key.startswith("AWS_"):
                del self.env[key]
        self.env.update(SHIPSENSE_STATE=self.directory.as_posix(), SHIPSENSE_OWNER=settings.owner)

    def docker(self, *arguments: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                ["docker", *arguments],
                cwd=ROOT,
                env=self.env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode:
                raise LocalFailure("DOCKER_COMMAND_FAILED")
            return result.stdout
        except OSError, subprocess.TimeoutExpired:
            raise LocalFailure("DOCKER_UNAVAILABLE") from None

    def local_engine(self) -> dict[str, Any]:
        if os.environ.get("DOCKER_HOST"):
            raise LocalFailure("REMOTE_DOCKER_REFUSED")
        context = json.loads(self.docker("context", "inspect"))
        endpoint = context[0]["Endpoints"]["docker"]["Host"]
        if not (endpoint.startswith("npipe:////./pipe/") or endpoint.startswith("unix:///")):
            raise LocalFailure("REMOTE_DOCKER_REFUSED")
        info: dict[str, Any] = json.loads(self.docker("info", "--format", "{{json .}}"))
        if info["OSType"] != "linux" or info["Architecture"] not in ("x86_64", "amd64"):
            raise LocalFailure("LINUX_AMD64_ENGINE_REQUIRED")
        return info

    def compose(self, *arguments: str) -> None:
        self.docker(
            "compose", "--project-name", PROJECT, "--file", str(COMPOSE), *arguments, timeout=180
        )

    def validate_ownership(self) -> dict[str, str]:
        self.local_engine()
        owned: dict[str, str] = {}
        # Inspect only this project's exact named resources, never globally prune.
        for kind, names in (
            ("container", [f"{PROJECT}-mongodb-1", f"{PROJECT}-storage-1"]),
            ("network", [f"{PROJECT}_fixture"]),
            (
                "volume",
                [f"{PROJECT}_{name}" for name in ("mongo-data", "mongo-config", "storage-data")],
            ),
        ):
            for name in names:
                listing = self.docker(
                    kind,
                    "ls",
                    "--filter",
                    f"name={name}",
                    "--format",
                    "{{.Name}}" if kind != "container" else "{{.Names}}",
                    *(["-a"] if kind == "container" else []),
                )
                if name not in listing.splitlines():
                    continue
                resource = json.loads(self.docker(kind, "inspect", name))[0]
                labels = resource["Config"]["Labels"] if kind == "container" else resource["Labels"]
                if not labels or labels.get("shipsense.owner") != self.settings.owner:
                    raise LocalFailure("UNOWNED_LOCAL_RESOURCE")
                if labels.get("com.docker.compose.project") != PROJECT:
                    raise LocalFailure("UNOWNED_LOCAL_RESOURCE")
                owned[name] = resource["Id"] if kind == "container" else name
        # A same-project extra container would make Compose teardown ambiguous.
        current = self.docker(
            "container",
            "ls",
            "-a",
            "--filter",
            f"label=com.docker.compose.project={PROJECT}",
            "--format",
            "{{.Names}}",
        )
        if set(current.splitlines()) - set(owned):
            raise LocalFailure("AMBIGUOUS_LOCAL_RESOURCES")
        return owned

    def preflight(self, owned: dict[str, str]) -> dict[str, int]:
        info = self.local_engine()
        if os.name == "nt":
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory * 1024",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode:
                raise LocalFailure("HOST_MEMORY_CHECK_FAILED")
            available = int(result.stdout.strip())
        else:
            sysconf = getattr(os, "sysconf")
            available = int(sysconf("SC_AVPHYS_PAGES") * sysconf("SC_PAGE_SIZE"))
        if info["MemTotal"] < 2 * 1024**3 or available < 1536 * 1024**2:
            raise LocalFailure("INSUFFICIENT_LOCAL_MEMORY")
        for service, port in (("mongodb", 37017), ("storage", 38333)):
            if f"{PROJECT}-{service}-1" in owned:
                continue
            try:
                with socket.socket() as listener:
                    listener.bind(("127.0.0.1", port))
            except OSError:
                raise LocalFailure("LOCAL_PORT_CONFLICT") from None
        return {"hostAvailableBytes": available, "engineLimitBytes": info["MemTotal"]}

    def up(self) -> dict[str, int]:
        owned = self.validate_ownership()
        measurement = self.preflight(owned)
        self.compose("up", "--detach", "--pull", "missing", "--no-build")
        self.validate_ownership()
        return measurement

    def down(self, *, reset: bool = False, confirmation: str | None = None) -> None:
        if reset and confirmation != PROJECT:
            raise LocalFailure("SYNTHETIC_RESET_CONFIRMATION_REQUIRED")
        self.validate_ownership()
        self.compose("down", *(["--volumes"] if reset else []))
