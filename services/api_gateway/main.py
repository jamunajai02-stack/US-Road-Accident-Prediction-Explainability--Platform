"""FastAPI Gateway application exposing prediction, explainability, and routing alert APIs."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from libs.common.config import ConfigLoader
from libs.common.logger import logger
from services.api_gateway.dependencies import get_service_container
from services.api_gateway.routes import health, hotspots, predict, route_check


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context initializing service dependencies at startup."""
    logger.info("Starting up Accident Prediction Platform API Gateway")
    # Warm up container and road graph
    get_service_container()
    yield
    logger.info("Shutting down API Gateway")


def create_app() -> FastAPI:
    """Factory function creating configured FastAPI application."""
    base_cfg = ConfigLoader.load("base")

    app = FastAPI(
        title="US Road Accident Prediction & Explainability Platform",
        description="Production-grade spatio-temporal accident forecasting, localized explainability, and hazard avoidance routing API.",
        version=base_cfg["app"]["version"],
        lifespan=lifespan,
    )

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(health.router)
    app.include_router(predict.router)
    app.include_router(route_check.router)
    app.include_router(hotspots.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.api_gateway.main:app", host="0.0.0.0", port=8000, reload=True)
