from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from co_sim.agents.api_gateway.routes import router as gateway_router
from co_sim.core import logging as logging_config
from co_sim.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging_config.configure_logging()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="CoSim API Gateway", version="0.1.0", lifespan=lifespan)

    @app.get("/healthz")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": "api-gateway"}

    app.include_router(gateway_router)
    return app


app = create_app()
