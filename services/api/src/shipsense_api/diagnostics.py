"""Public local diagnostics only; no customer data or provider authority."""

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

RequestId = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")]


class DiagnosticModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class VersionResponse(DiagnosticModel):
    service: Literal["shipsense-api"] = "shipsense-api"
    version: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")]
    apiVersion: Literal["v1"] = "v1"
    observedAt: AwareDatetime


class LivenessResponse(DiagnosticModel):
    status: Literal["alive"] = "alive"


class ReadinessResponse(DiagnosticModel):
    status: Literal["ready"] = "ready"


class ErrorDetail(DiagnosticModel):
    code: Literal["DEPENDENCY_UNAVAILABLE", "INVALID_REQUEST", "INTERNAL_ERROR"]
    message: Annotated[str, Field(min_length=1, max_length=160)]
    requestId: RequestId
    retryable: bool


class ApiError(DiagnosticModel):
    error: ErrorDetail


Probe = Callable[[], Awaitable[bool]]


class ReadinessGate:
    """Async, cancellation-cooperative probes; adapters own pools and shutdown.

    No adapters are installed by this slice. Never cache successes. Limit each
    probe to one second and at most four concurrent readiness requests. Missing,
    failed, timed-out or excess-capacity checks fail closed. Real adapter and
    outage/recovery acceptance belongs to the SCRUM-15 integration.
    """

    REQUIRED = frozenset({"mongodb", "storage", "queue"})

    def __init__(self, probes: Mapping[str, Probe] | None = None) -> None:
        self._probes = dict(probes or {})
        self._capacity = asyncio.Semaphore(4)

    async def ready(self) -> bool:
        if set(self._probes) != self.REQUIRED or self._capacity.locked():
            return False
        async with self._capacity:
            try:
                async with asyncio.timeout(3):
                    results = await asyncio.gather(
                        *(self._check(probe) for probe in self._probes.values())
                    )
                return all(results)
            except TimeoutError:
                return False

    @staticmethod
    async def _check(probe: Probe) -> bool:
        try:
            async with asyncio.timeout(1):
                return await probe() is True
        except Exception:
            # Dependency exception text may contain credentials or addresses.
            return False
