"""Route hazard evaluation and detour recommendation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from libs.schemas.alert import RouteRequest, RouteResponse
from services.api_gateway.dependencies import ServiceContainer, get_service_container

router = APIRouter(prefix="/v1", tags=["Navigation Route Risk & Detours"])


@router.post("/route-check", response_model=RouteResponse)
async def check_route_safety(
    request: RouteRequest,
    container: ServiceContainer = Depends(get_service_container),
) -> RouteResponse:
    """Evaluate a planned vehicle trip, identify hazardous hotspot segments, and return safe detour advisories."""
    try:
        # Run inference across road network
        preds, _ = await container.inference_pipeline.predict_corridor_risk()
        # Evaluate trip against predicted risks
        response = await container.route_alert_engine.evaluate_route(request, preds)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route evaluation failed: {e}")
