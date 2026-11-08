"""Credential-free process boundary; health/version integration arrives in P01.4."""

import os
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict


class FoundationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    service: Literal["shipsense-api"] = "shipsense-api"
    mode: Literal["local-foundation"] = "local-foundation"


def create_app() -> FastAPI:
    # This package has no production configuration or adapters yet.
    if os.environ.get("SHIPSENSE_PROFILE", "local") != "local":
        raise RuntimeError("SHIPSENSE_PROFILE must be local for the foundation.")
    app = FastAPI(title="ShipSense local foundation", version="0.1.0")

    @app.get("/foundation", response_model=FoundationResponse)
    def foundation() -> FoundationResponse:
        # Explicit public local diagnostic: no customer data or dependencies.
        return FoundationResponse()

    return app
