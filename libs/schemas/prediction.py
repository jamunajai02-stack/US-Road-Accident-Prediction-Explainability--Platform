"""Pydantic schemas for model predictions, edge risk assessments, and batch inference outputs."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RiskBand(str, Enum):
    LOW = "low"            # 0.0 - 0.30
    MODERATE = "moderate"  # 0.30 - 0.60
    HIGH = "high"          # 0.60 - 0.80
    SEVERE = "severe"      # 0.80 - 1.00


class ProbabilityOutput(BaseModel):
    """Calibrated probability output from the deep learning predictive core."""
    raw_probability: float = Field(..., ge=0.0, le=1.0, description="Raw uncalibrated sigmoid output")
    calibrated_probability: float = Field(..., ge=0.0, le=1.0, description="Prior-corrected probability P(accident) in [0, 1]")
    probability_percentage: float = Field(..., ge=0.0, le=100.0, description="Continuous 0-100% risk score")
    calibration_method: str = Field(default="elkan_log_odds", description="Applied calibration technique")


class EdgeRiskPrediction(BaseModel):
    """Forecasted accident risk for a single road edge in a 1-hour window."""
    edge_id: str = Field(..., description="Target road edge ID")
    timestamp: datetime = Field(..., description="Forecast window timestamp (UTC)")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated risk probability [0, 1]")
    risk_band: RiskBand = Field(..., description="Risk category (low, moderate, high, severe)")
    is_hotspot: bool = Field(default=False, description="True if risk >= hotspot threshold (default 0.80)")
    contributing_features: Dict[str, float] = Field(default_factory=dict, description="Key feature values at inference time")


class BatchInferenceResult(BaseModel):
    """Batch prediction result for a road network corridor or localized subgraph."""
    prediction_id: str = Field(..., description="Unique prediction batch trace ID")
    forecast_timestamp: datetime = Field(..., description="Target 1-hour window")
    num_edges_evaluated: int = Field(default=0, ge=0)
    num_hotspots_detected: int = Field(default=0, ge=0)
    inference_latency_ms: float = Field(default=0.0, ge=0.0, description="Total serving time in milliseconds")
    edge_predictions: List[EdgeRiskPrediction] = Field(default_factory=list, description="List of per-edge risk predictions")
