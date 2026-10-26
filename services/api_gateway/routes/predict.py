"""Prediction API endpoints for single-edge and corridor-wide accident risk queries."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from libs.schemas.graph import SubgraphQuery
from libs.schemas.prediction import BatchInferenceResult, EdgeRiskPrediction
from services.api_gateway.dependencies import ServiceContainer, get_service_container

router = APIRouter(prefix="/v1", tags=["Predictions & Risk Inference"])


@router.post("/predict", response_model=BatchInferenceResult)
async def predict_corridor_risk(
    edge_ids: Optional[List[str]] = None,
    container: ServiceContainer = Depends(get_service_container),
) -> BatchInferenceResult:
    """Predict short-horizon (next 1-hour) calibrated accident probability for requested road edges."""
    try:
        preds, latency_ms = await container.inference_pipeline.predict_corridor_risk(edge_ids)
        hotspot_count = sum(1 for p in preds if p.is_hotspot)

        return BatchInferenceResult(
            prediction_id=f"pred_{uuid.uuid4().hex[:8]}",
            forecast_timestamp=datetime.now(timezone.utc),
            num_edges_evaluated=len(preds),
            num_hotspots_detected=hotspot_count,
            inference_latency_ms=latency_ms,
            edge_predictions=preds,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")
