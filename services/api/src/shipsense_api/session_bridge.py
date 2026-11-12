"""Canonical session ports; no persistence adapter or in-memory runtime authority."""

import re
import time
from collections.abc import Callable
from typing import Literal, Protocol

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from shipsense_domain.sessions import SessionDenied as SessionDenied

from shipsense_api.service_credentials import (
    InvalidServiceCredential,
    Scope,
    ServiceKey,
    verify_service_credential,
)


class AuthorityUnavailable(Exception):
    pass


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    handle: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")


class SessionSnapshot(BaseModel):
    """Internal only: authority adapter must also check account state/epoch/revocation.

    This is not a principal context or authorization grant. Domain operations must
    resolve canonical state and permissions again, under their unit of work.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    createdAt: StrictInt = Field(ge=0)
    lastActivityAt: StrictInt = Field(ge=0)
    absoluteExpiresAt: StrictInt = Field(ge=0)
    idleExpiresAt: StrictInt = Field(ge=0)

    def check(self, now: int) -> None:
        if not (
            self.createdAt <= self.lastActivityAt <= now
            and self.createdAt < self.absoluteExpiresAt <= self.createdAt + 900
            and self.lastActivityAt < self.idleExpiresAt <= self.lastActivityAt + 600
            and now < min(self.absoluteExpiresAt, self.idleExpiresAt)
        ):
            raise SessionDenied()


class RevokedResponse(BaseModel):
    state: Literal["revoked"] = "revoked"


class BridgeFailure(BaseModel):
    state: Literal["denied", "unavailable"]
    requestId: str


class SessionAuthority(Protocol):
    async def resolve(self, handle: str, correlation_id: str) -> SessionSnapshot: ...

    async def revoke(self, handle: str, correlation_id: str) -> None:
        """Idempotent durable revoke plus audit; success only after confirmation."""
        ...


class UnavailableSessionAuthority:
    async def resolve(self, handle: str, correlation_id: str) -> SessionSnapshot:
        raise AuthorityUnavailable()

    async def revoke(self, handle: str, correlation_id: str) -> None:
        raise AuthorityUnavailable()


def session_router(
    authority: SessionAuthority | None = None,
    keys: dict[str, ServiceKey] | None = None,
    clock: Callable[[], int] = lambda: int(time.time()),
) -> APIRouter:
    # No environment switch can install a permissive adapter. Composition of a
    # durable authority and active public registry is a separately gated change.
    canonical = authority if authority is not None else UnavailableSessionAuthority()
    registry = dict(keys or {})
    router = APIRouter(
        prefix="/internal/v1/auth",
        tags=["Session bridge"],
        dependencies=[
            Depends(
                HTTPBearer(
                    auto_error=False,
                    scheme_name="BffServiceCredential",
                    description="Fixed RS256 BFF auth-only credential; never browser or worker authority.",
                )
            )
        ],
    )

    def failure(request: Request, status: int) -> JSONResponse:
        return JSONResponse(
            BridgeFailure(
                state="unavailable" if status == 503 else "denied",
                requestId=request.state.request_id,
            ).model_dump(),
            status_code=status,
        )

    def authenticate(request: Request, scope: Scope) -> None:
        values = request.headers.getlist("authorization")
        if len(values) != 1 or not re.fullmatch(r"Bearer [A-Za-z0-9_.-]{1,4096}", values[0]):
            raise InvalidServiceCredential()
        verify_service_credential(values[0][7:], scope, registry, clock())

    async def perform(request: Request, body: SessionRequest, scope: Scope) -> object:
        try:
            authenticate(request, scope)
        except InvalidServiceCredential:
            return failure(request, 401)
        try:
            if scope == "session:revoke":
                await canonical.revoke(body.handle, request.state.request_id)
                return RevokedResponse()
            snapshot = await canonical.resolve(body.handle, request.state.request_id)
            snapshot.check(clock())
            return snapshot
        except SessionDenied:
            return failure(request, 401)
        except Exception:
            return failure(request, 503)

    responses: dict[int | str, dict[str, object]] = {
        401: {"model": BridgeFailure},
        503: {"model": BridgeFailure},
    }

    @router.post("/session/resolve", response_model=SessionSnapshot, responses=responses)
    async def resolve(request: Request, body: SessionRequest) -> object:
        return await perform(request, body, "session:resolve")

    @router.post("/session/revoke", response_model=RevokedResponse, responses=responses)
    async def revoke(request: Request, body: SessionRequest) -> object:
        return await perform(request, body, "session:revoke")

    return router
