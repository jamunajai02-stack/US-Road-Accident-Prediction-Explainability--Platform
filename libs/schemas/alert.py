"""Pydantic schemas for route risk evaluation, detour recommendations, and client alert payloads."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from libs.schemas.explanation import NaturalLanguageExplanation


class Waypoint(BaseModel):
    """Geographic coordinate waypoint on a vehicle path."""
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    sequence_order: int = Field(default=0, ge=0)


class RouteRequest(BaseModel):
    """Client request to evaluate risk and obtain detour advisories for a navigation path."""
    route_id: str = Field(..., description="Unique trip or route identifier")
    origin: Waypoint = Field(..., description="Starting point coordinate")
    destination: Waypoint = Field(..., description="Target destination coordinate")
    departure_time: datetime = Field(default_factory=datetime.utcnow, description="Scheduled departure timestamp (UTC)")
    waypoints: List[Waypoint] = Field(default_factory=list, description="Optional intermediate route waypoints")


class DetourOption(BaseModel):
    """Alternative safe route bypassing dangerous hotspots."""
    detour_id: str = Field(..., description="Unique detour identifier")
    risk_reduction_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage reduction in total route accident risk")
    additional_distance_km: float = Field(..., ge=0.0, description="Additional distance compared to primary route")
    additional_time_minutes: float = Field(..., ge=0.0, description="Additional travel time in minutes")
    geometry_polyline: str = Field(..., description="Encoded polyline or GeoJSON coordinate string for detour")


class AlertPayload(BaseModel):
    """Complete real-time incident/hazard warning payload dispatched to vehicles or traffic centers."""
    alert_id: str = Field(..., description="Unique alert UUID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    hotspot_cluster_id: str = Field(..., description="Identified high-risk cluster ID")
    hazard_location: Waypoint = Field(..., description="Centroid or critical intersection coordinate")
    max_risk_probability: float = Field(..., ge=0.80, le=1.0, description="Max predicted probability in hotspot")
    explanation: NaturalLanguageExplanation = Field(..., description="Phase 4 human-readable causative explanation")
    suggested_detour: Optional[DetourOption] = Field(default=None, description="Valhalla calculated alternate safe path")
    affected_edge_ids: List[str] = Field(default_factory=list)


class RouteResponse(BaseModel):
    """Full risk report for a requested vehicle route."""
    route_id: str = Field(..., description="Associated route identifier")
    overall_safety_status: str = Field(..., description="'SAFE' | 'CAUTION' | 'HAZARDOUS'")
    max_risk_score: float = Field(..., ge=0.0, le=1.0)
    active_alerts: List[AlertPayload] = Field(default_factory=list, description="Triggered alerts for high hazard zones")
    recommended_route_geometry: str = Field(..., description="Optimal selected route polyline/GeoJSON")
