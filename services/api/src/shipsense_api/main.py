"""Credential-free local diagnostic API; no domain authorization exceptions."""

import logging
import os
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Header, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from shipsense_domain.models import IdentityContract
from starlette.exceptions import HTTPException

from shipsense_api.diagnostics import (
    ApiError,
    ErrorDetail,
    LivenessResponse,
    ReadinessGate,
    ReadinessResponse,
    VersionResponse,
)
from shipsense_api.hosted import HostedReadiness

LOGGER = logging.getLogger("shipsense.diagnostics")
LOGGER.setLevel(logging.INFO)
if not LOGGER.handlers:
    LOGGER.addHandler(logging.StreamHandler())
LOGGER.propagate = False
REQUEST_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
VERSION = "0.1.0-dev"


def safe_error(request: Request, status: int) -> JSONResponse:
    code: Literal["DEPENDENCY_UNAVAILABLE", "INVALID_REQUEST", "INTERNAL_ERROR"]
    if status == 503:
        code, message = "DEPENDENCY_UNAVAILABLE", "A required dependency is unavailable."
    elif status >= 500:
        code, message = "INTERNAL_ERROR", "The request could not be completed."
    else:
        code, message = "INVALID_REQUEST", "The request is invalid."
    body = ApiError(
        error=ErrorDetail(
            code=code,
            message=message,
            requestId=request.state.request_id,
            retryable=status >= 500,
        )
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=status)


def error_contract(status: int) -> dict[str, object]:
    example = {
        "error": {
            "code": "DEPENDENCY_UNAVAILABLE"
            if status == 503
            else ("INTERNAL_ERROR" if status == 500 else "INVALID_REQUEST"),
            "message": "A required dependency is unavailable."
            if status == 503
            else (
                "The request could not be completed."
                if status == 500
                else "The request is invalid."
            ),
            "requestId": "req-local-001",
            "retryable": status >= 500,
        }
    }
    return {"model": ApiError, "content": {"application/json": {"example": example}}}


class FoundationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    service: Literal["shipsense-api"] = "shipsense-api"
    mode: Literal["local-foundation"] = "local-foundation"


def create_app(readiness: ReadinessGate | None = None) -> FastAPI:
    # This package has no production configuration or adapters yet.
    if os.environ.get("SHIPSENSE_PROFILE", "local") != "local":
        raise RuntimeError("SHIPSENSE_PROFILE must be local for the foundation.")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        runtime: HostedReadiness | None = None
        if readiness is None:
            try:
                runtime = await HostedReadiness.from_environment(os.environ)
                app.state.readiness_gate = runtime.gate
            except Exception:
                # Invalid configuration keeps public diagnostics available. Never
                # log validation errors, paths, dependency addresses or secrets.
                LOGGER.info("dependency_adapters=unavailable")
        app.state.dependency_runtime = runtime
        try:
            yield
        finally:
            app.state.readiness_gate = ReadinessGate()
            app.state.dependency_runtime = None
            if runtime is not None:
                try:
                    await runtime.close()
                except Exception:
                    LOGGER.info("dependency_adapters=shutdown_failed")

    app = FastAPI(
        title="ShipSense local diagnostics",
        version="0.1.0",
        responses={422: error_contract(422), 500: error_contract(500)},
        lifespan=lifespan,
    )
    app.state.readiness_gate = readiness if readiness is not None else ReadinessGate()

    @app.middleware("http")
    async def correlation(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.getlist("x-request-id")
        valid = len(supplied) == 1 and re.fullmatch(REQUEST_ID_PATTERN, supplied[0]) is not None
        request.state.request_id = supplied[0] if valid else "req-" + uuid4().hex
        if supplied and not valid:
            response: Response = safe_error(request, 422)
        else:
            try:
                response = await call_next(request)
            except Exception:
                response = safe_error(request, 500)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        # Never log URL/query/header values, rejected payloads or exception text.
        LOGGER.info("request_id=%s status=%d", request.state.request_id, response.status_code)
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        return safe_error(request, 422)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return safe_error(request, exc.status_code)

    @app.get(
        "/api/v1/version",
        response_model=VersionResponse,
        responses={
            200: {
                "content": {
                    "application/json": {
                        "example": {
                            "service": "shipsense-api",
                            "version": VERSION,
                            "apiVersion": "v1",
                            "observedAt": "2026-11-08T00:00:00Z",
                        }
                    }
                }
            }
        },
    )
    async def version(
        x_request_id: str | None = Header(
            default=None, min_length=1, max_length=64, pattern=REQUEST_ID_PATTERN
        ),
    ) -> VersionResponse:
        return VersionResponse(version=VERSION, observedAt=datetime.now(UTC))

    @app.get(
        "/health/live",
        response_model=LivenessResponse,
        responses={200: {"content": {"application/json": {"example": {"status": "alive"}}}}},
    )
    async def live() -> LivenessResponse:
        return LivenessResponse()

    @app.get(
        "/health/ready",
        response_model=ReadinessResponse,
        responses={
            503: error_contract(503),
            200: {"content": {"application/json": {"example": {"status": "ready"}}}},
        },
    )
    async def ready(request: Request) -> ReadinessResponse | JSONResponse:
        if not await app.state.readiness_gate.ready():
            return safe_error(request, 503)
        return ReadinessResponse()

    @app.get("/foundation", response_model=FoundationResponse)
    def foundation() -> FoundationResponse:
        # Explicit public local diagnostic: no customer data or dependencies.
        return FoundationResponse()

    # Publish shared schema contracts without exposing an unauthenticated domain
    # route or suggesting that sessions/administration have been implemented.
    schema = app.openapi()
    identity_schema = IdentityContract.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )
    definitions = identity_schema.pop("$defs", {})
    schema["components"]["schemas"].update(definitions)
    schema["components"]["schemas"]["IdentityContract"] = identity_schema
    return app
