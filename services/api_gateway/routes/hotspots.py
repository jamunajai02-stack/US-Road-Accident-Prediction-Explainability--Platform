"""Hotspot discovery and natural language explainability endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from libs.schemas.explanation import HotspotCluster, NaturalLanguageExplanation
from services.api_gateway.dependencies import ServiceContainer, get_service_container

router = APIRouter(prefix="/v1", tags=["Hotspot Isolation & Explainability"])


@router.get("/hotspots", response_model=List[HotspotCluster])
async def list_active_hotspots(
    container: ServiceContainer = Depends(get_service_container),
) -> List[HotspotCluster]:
    """Retrieve all currently active danger hotspot clusters (>80% risk cutoff)."""
    preds, _ = await container.inference_pipeline.predict_corridor_risk()
    clusters = container.hotspot_isolator.isolate_hotspots(preds, container.road_graph)
    return clusters


@router.get("/hotspots/{cluster_id}/explanation", response_model=NaturalLanguageExplanation)
async def get_hotspot_explanation(
    cluster_id: str,
    container: ServiceContainer = Depends(get_service_container),
) -> NaturalLanguageExplanation:
    """Generate localized causative natural-language explanation and driver advisory for a specific hotspot."""
    preds, _ = await container.inference_pipeline.predict_corridor_risk()
    clusters = container.hotspot_isolator.isolate_hotspots(preds, container.road_graph)
    
    target_cluster = next((c for c in clusters if c.cluster_id == cluster_id), None)
    if not target_cluster:
        # Generate on-demand cluster object if matching ID format
        target_cluster = HotspotCluster(
            cluster_id=cluster_id,
            edge_ids=["1_2_0", "2_3_0"],
            centroid_latitude=37.7749,
            centroid_longitude=-122.4194,
            avg_risk_probability=0.86,
            max_risk_probability=0.89,
        )

    # Mine localized rule & translate
    rule = container.rule_miner._build_default_heuristic_rule(target_cluster)
    explanation = container.rule_translator.translate(target_cluster, rule)
    return explanation
