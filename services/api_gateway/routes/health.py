"""Health probe and telemetry status endpoints."""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends
from services.api_gateway.dependencies import ServiceContainer, get_service_container

router = APIRouter(tags=["Health & System Telemetry"])


@router.get("/health")
async def health_check(container: ServiceContainer = Depends(get_service_container)) -> Dict[str, Any]:
    """Liveness and readiness probe for Kubernetes / Docker Compose health checks."""
    return {
        "status": "HEALTHY",
        "service": "accident-prediction-platform-api",
        "version": container.base_cfg["app"]["version"],
        "environment": container.base_cfg["app"]["env"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graph_nodes": container.road_graph.number_of_nodes(),
        "graph_edges": container.road_graph.number_of_edges(),
    }


@router.get("/metrics")
async def get_metrics(container: ServiceContainer = Depends(get_service_container)) -> Dict[str, Any]:
    """System metrics and model cache telemetry."""
    return {
        "active_feature_cache": type(container.feature_cache).__name__,
        "hotspot_cutoff": container.thresholds_cfg["thresholds"]["hotspot"]["probability_cutoff"],
        "routing_engine": type(container.routing_engine).__name__,
    }
