"""Real API/built-web diagnostics, optionally against existing hosted MongoDB/R2.

No services are provisioned, seeded, reset or stopped. Hosted access is read-only.
Missing hosted configuration fails explicitly; it is never a skipped live pass.
"""

import argparse
import asyncio
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PureWindowsPath
from typing import Any

import httpx
from botocore.exceptions import ClientError
from shipsense_api.diagnostics import ApiError, VersionResponse
from shipsense_api.hosted import HostedReadiness, HostedSettings
from shipsense_local.adapters import BoundedObjects, private_s3
from shipsense_local.config import ROOT, LocalFailure

HOSTED_KEYS = tuple("SHIPSENSE_" + field.upper() for field in HostedSettings.model_fields)


def evidence_directory() -> Path:
    supplied = os.environ.get("SHIPSENSE_EVIDENCE_DIR")
    base = Path(supplied) if supplied else Path(tempfile.gettempdir())
    if (
        not base.is_absolute()
        or str(base).replace("\\", "/").startswith("//")
        or PureWindowsPath(str(base)).drive.startswith("\\")
        or any(p.is_symlink() or p.is_junction() for p in (base, *base.parents))
        or base.resolve().is_relative_to(ROOT)
    ):
        raise LocalFailure("UNSAFE_EVIDENCE_DIRECTORY")
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    return Path(tempfile.mkdtemp(prefix="shipsense-smoke-", dir=base))


def clean_environment() -> dict[str, str]:
    # Provider settings are added only to the hosted API, never the web/browser.
    allowed = {
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
        "SYSTEMDRIVE",
        "COMSPEC",
        "PROGRAMDATA",
        "ALLUSERSPROFILE",
        "LOCALAPPDATA",
        "APPDATA",
        "USERPROFILE",
        "HOME",
        "TEMP",
        "TMP",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "SHIPSENSE_CHROME",
    }
    result = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    result.update(SHIPSENSE_PROFILE="local", NEXT_TELEMETRY_DISABLED="1", PYTHONUTF8="1")
    return result


class Child:
    def __init__(self, command: list[str], env: dict[str, str], *, protocol: bool = False) -> None:
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        self.process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdin=subprocess.PIPE if protocol else subprocess.DEVNULL,
            stdout=subprocess.PIPE if protocol else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            creationflags=creationflags,
            start_new_session=sys.platform != "win32",
        )

    def exchange(self, command: str | None, expected: str) -> None:
        if command is not None:
            assert self.process.stdin is not None
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
        assert self.process.stdout is not None
        # The browser controller has its own bounded command and lifetime timers.
        if self.process.stdout.readline().strip() != expected:
            raise LocalFailure("BROWSER_SMOKE_FAILED")

    def stop(self) -> None:
        if self.process.poll() is None:
            if sys.platform == "win32":
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                getattr(os, "killpg")(self.process.pid, signal.SIGTERM)
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=15,
                    )
                else:
                    getattr(os, "killpg")(self.process.pid, getattr(signal, "SIGKILL"))
                self.process.wait(timeout=10)
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                stream.close()


def assert_free(port: int) -> None:
    try:
        with socket.socket() as listener:
            # POSIX servers reuse closed connections in TIME_WAIT. Windows
            # instead needs exclusive binding: SO_REUSEADDR can share a live
            # listener there. listen() also detects a competing POSIX listener
            # when both sockets opted into address reuse; never use REUSEPORT.
            if sys.platform == "win32":
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", port))
            listener.listen(1)
    except OSError:
        raise LocalFailure("SMOKE_PORT_CONFLICT") from None


def cleanup(directory: Path, children: list[Child], browser: Child | None) -> None:
    if browser is not None and browser.process.poll() is None:
        assert browser.process.stdin is not None
        try:
            browser.process.stdin.write("quit\n")
            browser.process.stdin.flush()
            browser.process.wait(timeout=10)
        except OSError, subprocess.TimeoutExpired:
            pass
    stop_failed = False
    for child in reversed(children):
        try:
            child.stop()
        except OSError, subprocess.SubprocessError:
            stop_failed = True
    ports_free = True
    for port in (8000, 3000):
        try:
            assert_free(port)
        except LocalFailure:
            ports_free = False
    (directory / "cleanup.json").write_text(
        json.dumps({"ownedProcessesStopped": not stop_failed, "portsAvailable": ports_free}) + "\n"
    )
    if stop_failed:
        raise LocalFailure("OWNED_PROCESS_CLEANUP_FAILED")
    if not ports_free:
        raise LocalFailure("SMOKE_PORT_CONFLICT")


def request(path: str, expected: int, *, web: bool = False) -> dict[str, Any]:
    origin = "http://127.0.0.1:3000" if web else "http://127.0.0.1:8000"
    with httpx.Client(trust_env=False, timeout=6) as client:
        response = client.get(origin + path, headers={"X-Request-ID": "smoke-reference"})
    if response.status_code != expected or response.headers.get("cache-control") != "no-store":
        raise LocalFailure("SMOKE_GATE_FAILED")
    body: dict[str, Any] = response.json()
    if expected >= 400:
        error = ApiError.model_validate(body).error
        if error.requestId != response.headers.get("x-request-id"):
            raise LocalFailure("SMOKE_CORRELATION_FAILED")
    return body


def wait_http(path: str, expected: int, *, web: bool = False) -> None:
    end = time.monotonic() + 30
    while time.monotonic() < end:
        try:
            request(path, expected, web=web)
            return
        except httpx.HTTPError, LocalFailure:
            time.sleep(0.2)
    raise LocalFailure("SMOKE_STARTUP_FAILED")


def start_api(env: dict[str, str]) -> Child:
    assert_free(8000)
    return Child(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "shipsense_api.main:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--no-access-log",
        ],
        env,
    )


async def verify_hosted_access(environment: dict[str, str]) -> None:
    settings = HostedSettings.from_environment(environment)
    runtime = await HostedReadiness.from_environment(environment)
    try:
        # Allow bounded cold DNS/TLS discovery without relaxing individual probe
        # deadlines. A persistent denial or outage must still fail the command.
        for attempt in range(3):
            if await runtime.clients.mongo_probe():
                break
            if attempt < 2:
                await asyncio.sleep(0.15)
        else:
            raise LocalFailure("HOSTED_MONGODB_READ_FAILED")
        if not await runtime.clients.objects.probe():
            raise LocalFailure("HOSTED_R2_ACCESS_FAILED")
        for mode in ("anonymous", "wrong-key"):
            denied_objects = BoundedObjects(
                settings.r2_bucket,
                private_s3(
                    settings.r2_endpoint,
                    "auto",
                    "0" * 32,
                    "0" * 64,
                    unsigned=mode == "anonymous",
                ),
            )
            try:

                def denied() -> bool:
                    try:
                        # HEAD hides R2's auth error body. Request zero keys to
                        # distinguish authentication rejection from bad requests
                        # without retrieving object names or customer contents.
                        denied_objects._client.list_objects_v2(Bucket=settings.r2_bucket, MaxKeys=0)
                    except ClientError as error:
                        status = error.response["ResponseMetadata"]["HTTPStatusCode"]
                        detail = error.response.get("Error", {})
                        return (
                            status in {401, 403}
                            and detail.get("Code")
                            in {
                                "Unauthorized",
                                "AccessDenied",
                                "SignatureDoesNotMatch",
                                "InvalidAccessKeyId",
                            }
                        ) or (
                            mode == "anonymous"
                            and status == 400
                            and detail.get("Code") == "InvalidArgument"
                            and detail.get("Message") == "Authorization"
                        )
                    return False

                if not await denied_objects.call(denied):
                    raise LocalFailure("HOSTED_R2_DENIAL_NOT_PROVED")
            finally:
                await denied_objects.close()
    finally:
        await runtime.close()


def smoke(directory: Path, *, hosted: bool, fail_upstream: bool) -> None:
    env = clean_environment()
    configured = env.copy()
    if hosted:
        HostedSettings.from_environment(os.environ)
        configured.update({key: os.environ[key] for key in HOSTED_KEYS if key in os.environ})
        asyncio.run(verify_hosted_access(configured))
    children: list[Child] = []
    browser: Child | None = None
    primary_failed = False
    try:
        assert_free(3000)
        # Check missing and malformed configuration against actual HTTP. The
        # malformed marker is rejected before DNS/client creation.
        for values in ({}, {"SHIPSENSE_MONGODB_URI": "invalid-config"}):
            api = start_api(env | values)
            children.append(api)
            wait_http("/health/ready", 503)
            request("/health/live", 200)
            request("/api/v1/version", 200)
            api.stop()
        api = start_api(configured)
        children.append(api)
        wait_http("/health/ready", 200 if hosted else 503)
        version = VersionResponse.model_validate(request("/api/v1/version", 200))
        web = Child(
            [
                "node",
                "node_modules/next/dist/bin/next",
                "start",
                "apps/web",
                "--hostname",
                "127.0.0.1",
                "--port",
                "3000",
            ],
            env | {"SHIPSENSE_API_ORIGIN": "http://127.0.0.1:8000"},
        )
        children.append(web)
        wait_http("/api/foundation", 200, web=True)
        if (
            VersionResponse.model_validate(request("/api/foundation", 200, web=True)).version
            != version.version
        ):
            raise LocalFailure("WEB_API_VERSION_MISMATCH")
        browser = Child(["node", "scripts/browser-smoke.mjs", str(directory)], env, protocol=True)
        children.append(browser)
        browser.exchange(None, "BROWSER_READY")
        browser.exchange("connected", "BROWSER_CONNECTED")
        api.stop()
        request("/api/foundation", 502, web=True)
        browser.exchange("unavailable", "BROWSER_UNAVAILABLE")
        if fail_upstream:
            try:
                request("/api/foundation", 200, web=True)
            except LocalFailure as error:
                if str(error) == "SMOKE_GATE_FAILED":
                    raise LocalFailure("UPSTREAM_SUCCESS_GATE_REJECTED") from None
                raise
        api = start_api(configured)
        children.append(api)
        wait_http("/health/ready", 200 if hosted else 503)
        request("/api/foundation", 200, web=True)
        browser.exchange("recovered", "BROWSER_RECOVERED")
    except BaseException:
        primary_failed = True
        raise
    finally:
        try:
            cleanup(directory, children, browser)
        except Exception:
            # Preserve the original failure/cancellation; cleanup.json records
            # any secondary stop/port failure without exposing exception data.
            if not primary_failed:
                raise
    (directory / "smoke.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "profile": "hosted" if hosted else "credential-free",
                "hostedAccessVerified": hosted,
                "providerWrites": 0,
                "unconfiguredReady": 503,
                "configuredReady": 200 if hosted else None,
                "browserRecovery": True,
            }
        )
        + "\n"
    )
    print(
        "Hosted integration passed." if hosted else "Credential-free API/web smoke passed.",
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hosted", action="store_true")
    parser.add_argument("--fail-upstream", action="store_true")
    args = parser.parse_args()

    def interrupted(_number: int, _frame: Any) -> None:
        raise LocalFailure("SMOKE_CANCELLED")

    signal.signal(signal.SIGTERM, interrupted)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(getattr(signal, "SIGBREAK"), interrupted)
    try:
        directory = evidence_directory()
        smoke(directory, hosted=args.hosted, fail_upstream=args.fail_upstream)
        return 0
    except (Exception, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, LocalFailure) else "SMOKE_OPERATION_FAILED"
        print(json.dumps({"error": code}), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
