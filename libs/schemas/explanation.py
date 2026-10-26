"""Pydantic schemas for localized hotspot explainability, decision tree rule mining, and natural language outputs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DecisionRule(BaseModel):
    """Single decision tree split condition extracted from a localized micro-tree."""
    feature_name: str = Field(..., description="Feature involved in split (e.g., precipitation_mm, curvature)")
    operator: str = Field(..., description="Comparison operator: '>', '<=', '>=', '<'")
    threshold_value: float = Field(..., description="Numeric threshold value of the decision boundary")
    feature_importance: float = Field(default=0.0, ge=0.0, le=1.0, description="Gini/Entropy importance of feature")


class HotspotRule(BaseModel):
    """Structured rule defining the exact multi-condition causative pattern for a danger hotspot."""
    rule_id: str = Field(..., description="Rule identifier")
    cluster_id: str = Field(..., description="Associated hotspot cluster ID")
    conditions: List[DecisionRule] = Field(..., description="Ordered list of decision split rules")
    rule_precision: float = Field(..., ge=0.0, le=1.0, description="Precision / purity of this rule path")
    support_sample_count: int = Field(..., ge=1, description="Number of historical samples supporting rule")


class HotspotCluster(BaseModel):
    """Spatially connected cluster of high-risk road segments (probability > 80%)."""
    cluster_id: str = Field(..., description="Unique cluster ID (e.g., hotspot_cluster_42)")
    edge_ids: List[str] = Field(..., description="Road edge IDs belonging to this danger cluster")
    centroid_latitude: float = Field(..., ge=-90.0, le=90.0)
    centroid_longitude: float = Field(..., ge=-180.0, le=180.0)
    avg_risk_probability: float = Field(..., ge=0.80, le=1.0, description="Average risk score in cluster")
    max_risk_probability: float = Field(..., ge=0.80, le=1.0)
    radius_meters: float = Field(default=500.0, ge=0.0)
    top_rule: Optional[HotspotRule] = Field(default=None)


class NaturalLanguageExplanation(BaseModel):
    """Human-readable causative explanation and advisory generated for drivers and operators."""
    cluster_id: str = Field(..., description="Hotspot cluster identifier")
    summary: str = Field(..., description="Concise headline explanation (e.g., 'Severe Hydroplaning & Glare Hazard')")
    causative_statement: str = Field(..., description="Full causative natural language sentence")
    contributing_factors: List[str] = Field(..., description="Bullet points of contributing physical/weather factors")
    driver_advisory: str = Field(..., description="Actionable driver recommendation (e.g., 'Reduce speed to 35 mph')")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
