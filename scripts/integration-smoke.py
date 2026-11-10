"""Fresh, owned CI-only seeded smoke. Never adopts or resets developer state."""

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
from pathlib import Path
from typing import Any, Final

import httpx
from shipsense_api.diagnostics import ApiError, VersionResponse
from shipsense_local.adapters import LocalClients
from shipsense_local.cli import queue_smoke, wait_for_services
from shipsense_local.config import ROOT, LocalFailure, load_settings, state_path
from shipsense_local.fixtures import seed_all
from shipsense_local.stack import LocalStack, initialize, private_directory

CI_PROJECT: Final = "shipsense-ci-p01"


def evidence_directory() -> Path:
    supplied = os.environ.get("SHIPSENSE_EVIDENCE_DIR")
    path = (
        state_path(Path(supplied))
        if supplied
        else Path(tempfile.mkdtemp(prefix="shipsense-smoke-"))
    )
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def clean_environment() -> dict[str, str]:
    # An allowlist, not a list of guessed credential names. No provider/agent
    # tokens, host cloud profiles or inherited app/Compose configuration.
    allowed = {
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
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
        "DOCKER_CONFIG",
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
            listener.bind(("127.0.0.1", port))
    except OSError:
        raise LocalFailure("SMOKE_PORT_CONFLICT") from None


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


def start_api(env: dict[str, str], state: Path | None = None) -> Child:
    assert_free(8000)
    options = env.copy()
    if state is not None:
        options["SHIPSENSE_DEPENDENCIES"] = "test-fixtures"
        options["SHIPSENSE_LOCAL_STATE_DIR"] = str(state)
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
        options,
    )


def discard_private_state(state: Path, owner: str) -> None:
    if load_settings(state).owner != owner:
        raise LocalFailure("UNOWNED_CI_ATTEMPT")
    names = ("local.json", "s3.json", "mongo-app.json", "mongo-root.txt")
    if {item.name for item in state.iterdir()} != set(names):
        raise LocalFailure("AMBIGUOUS_CI_STATE")
    for name in names:
        (state / name).unlink()
    state.rmdir()


def cleanup(directory: Path) -> None:
    receipt = directory / "attempt.json"
    if not receipt.exists():
        return
    data = json.loads(receipt.read_text())
    # Only our exact fixed private child path; never a caller-provided reset target.
    state = state_path(directory / "private-state")
    settings = load_settings(state)
    if data != {"namespace": CI_PROJECT, "owner": settings.owner}:
        raise LocalFailure("UNOWNED_CI_ATTEMPT")
    stack = LocalStack(state, settings, project=CI_PROJECT)
    stack.down(reset=True, confirmation=CI_PROJECT)
    if stack.validate_ownership():
        raise LocalFailure("CI_CLEANUP_INCOMPLETE")
    receipt.unlink()
    # Keep private state until safe resource teardown is evidenced. Removal is
    # deliberately limited to the known files generated by initialize().
    discard_private_state(state, settings.owner)
    (directory / "cleanup.json").write_text(
        json.dumps({"ciResourcesRemaining": 0, "developerStateTouched": False}) + "\n"
    )


async def seed_and_verify(stack: LocalStack) -> None:
    await wait_for_services(stack.settings)
    async with LocalClients(stack.settings) as clients:
        if await seed_all(clients) != {"inserted": 6, "unchanged": 0}:
            raise LocalFailure("FRESH_CI_SEED_REQUIRED")
        if await seed_all(clients) != {"inserted": 0, "unchanged": 6}:
            raise LocalFailure("IDEMPOTENT_CI_SEED_REQUIRED")
    if (await queue_smoke())["effects"] != 0:
        raise LocalFailure("NO_EFFECT_QUEUE_REQUIRED")


def real_tests(env: dict[str, str], state: Path) -> None:
    options = {**env, "SHIPSENSE_TEST_STATE": str(state)}
    for directory, pattern in (
        ("packages/local-core/tests", "test_integration.py"),
        ("services/api/tests", "test_readiness_integration.py"),
    ):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                directory,
                "-p",
                pattern,
                "-v",
            ],
            cwd=ROOT,
            env=options,
            capture_output=True,
            timeout=180,
        )
        if result.returncode or b"skipped" in result.stderr or b"Ran 0 tests" in result.stderr:
            raise LocalFailure("REAL_INTEGRATION_FAILED")
    print("Real adapter/readiness integrations: 10 passed, none skipped.", flush=True)


def smoke(directory: Path, *, fail_upstream: bool = False) -> None:
    if any(
        (directory / name).exists() for name in ("attempt.json", "private-state", "browser-profile")
    ):
        raise LocalFailure("STALE_CI_ATTEMPT_REFUSED")
    env = clean_environment()
    for port in (8000, 3000):
        assert_free(port)
    state = directory / "private-state"
    settings = initialize(state, project=CI_PROJECT)
    # Check before writing a cleanup receipt; another owner's resources are
    # never made eligible for cleanup by a failed preflight.
    try:
        stack = LocalStack(state, settings, project=CI_PROJECT)
        if stack.validate_ownership():
            raise LocalFailure("STALE_CI_RESOURCES_REFUSED")
        stack.preflight({})
    except BaseException:
        # No launch has occurred; discard only the freshly generated credentials.
        discard_private_state(state, settings.owner)
        raise
    (directory / "attempt.json").write_text(
        json.dumps({"namespace": CI_PROJECT, "owner": settings.owner}) + "\n"
    )
    children: list[Child] = []
    browser: Child | None = None
    try:
        stack.up()
        try:
            asyncio.run(seed_and_verify(stack))
        except Exception:
            # Inspect only ownership-verified fixture services. Never publish raw
            # provider/container output: classify known bootstrap errors only.
            stack.validate_ownership()
            denied = False
            classification = {}
            for service in ("mongodb", "storage"):
                output = stack.docker(
                    "compose",
                    "--project-name",
                    CI_PROJECT,
                    "--file",
                    str(ROOT / "infra/local/compose.yaml"),
                    "logs",
                    "--no-color",
                    "--tail",
                    "80",
                    service,
                ).lower()
                permission = "permission denied" in output or "eacces" in output
                denied = denied or permission
                classification[service] = {
                    "permissionDenied": permission,
                    "mentions": [
                        name
                        for name in (
                            "/run/secrets",
                            "/run/shipsense",
                            "/docker-entrypoint-initdb.d",
                            "/data/db",
                            "/tmp",
                            "/proc",
                            "file_env",
                            "mongosh",
                        )
                        if name in output
                    ],
                }
            (directory / "bootstrap-diagnostic.json").write_text(json.dumps(classification) + "\n")
            raise LocalFailure(
                "FIXTURE_BOOTSTRAP_PERMISSION_DENIED" if denied else "FIXTURE_BOOTSTRAP_FAILED"
            ) from None
        print("Fresh CI services seeded; private access verified.", flush=True)
        real_tests(env, state)
        default_api = start_api(env)
        children.append(default_api)
        wait_http("/health/ready", 503)
        request("/health/live", 200)
        default_api.stop()
        api = start_api(env, state)
        children.append(api)
        wait_http("/health/ready", 200)
        version = VersionResponse.model_validate(request("/api/v1/version", 200))
        assert_free(3000)
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
            {**env, "SHIPSENSE_API_ORIGIN": "http://127.0.0.1:8000"},
        )
        children.append(web)
        wait_http("/api/foundation", 200, web=True)
        if (
            VersionResponse.model_validate(request("/api/foundation", 200, web=True)).version
            != version.version
        ):
            raise LocalFailure("WEB_API_VERSION_MISMATCH")
        for service in ("mongodb", "storage"):
            stack.validate_ownership()
            stack.compose("stop", service)
            try:
                started = time.monotonic()
                request("/health/ready", 503)
                if time.monotonic() - started > 2:
                    raise LocalFailure("READINESS_DEADLINE_FAILED")
                request("/health/live", 200)
                request("/api/foundation", 200, web=True)
            finally:
                stack.compose("start", service)
            wait_http("/health/ready", 200)
        private_directory(directory / "browser-profile")
        browser = Child(["node", "scripts/browser-smoke.mjs", str(directory)], env, protocol=True)
        children.append(browser)
        browser.exchange(None, "BROWSER_READY")
        browser.exchange("connected", "BROWSER_CONNECTED")
        api.stop()
        request("/api/foundation", 502, web=True)
        browser.exchange("unavailable", "BROWSER_UNAVAILABLE")
        if fail_upstream:
            # Exercise the actual required success gate while its upstream is
            # stopped; the caller must observe failure, never a skipped pass.
            try:
                request("/api/foundation", 200, web=True)
            except LocalFailure as error:
                if str(error) == "SMOKE_GATE_FAILED":
                    raise LocalFailure("UPSTREAM_SUCCESS_GATE_REJECTED") from None
                raise
        api = start_api(env, state)
        children.append(api)
        wait_http("/health/ready", 200)
        request("/api/foundation", 200, web=True)
        browser.exchange("recovered", "BROWSER_RECOVERED")
        print(
            "Real seeded built-web/API/dependency/browser outage and recovery passed.", flush=True
        )
        (directory / "smoke.json").write_text(
            json.dumps(
                {
                    "status": "passed",
                    "realIntegrationCases": 10,
                    "freshSeed": 6,
                    "effects": 0,
                    "defaultReady": 503,
                    "configuredReady": 200,
                    "dependencyRecovery": True,
                    "browserRecovery": True,
                }
            )
            + "\n"
        )
    finally:
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
        cleanup(directory)
        if stop_failed:
            raise LocalFailure("OWNED_PROCESS_CLEANUP_FAILED")
        for port in (8000, 3000, 37017, 38333):
            assert_free(port)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--fail-upstream", action="store_true")
    args = parser.parse_args()
    directory = evidence_directory()

    def interrupted(_number: int, _frame: Any) -> None:
        raise LocalFailure("SMOKE_CANCELLED")

    signal.signal(signal.SIGTERM, interrupted)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(getattr(signal, "SIGBREAK"), interrupted)
    try:
        if args.cleanup:
            cleanup(directory)
        else:
            smoke(directory, fail_upstream=args.fail_upstream)
        return 0
    except (Exception, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, LocalFailure) else "SMOKE_OPERATION_FAILED"
        print(json.dumps({"error": code}), flush=True)
        (directory / "failure.json").write_text(json.dumps({"error": code}) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
