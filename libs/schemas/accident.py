"""Pydantic v2 schemas for raw accidents, negative samples, and enriched dataset records."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class AccidentEvent(BaseModel):
    """Raw accident event ingested from Kaggle or live streaming sources.
    Note (Patch 1): In Phase 1, spatial indexing attaches h3_cell only. Road edge snapping happens in Phase 2.
    """
    id: str = Field(..., description="Deterministic unique identifier for the accident record")
    timestamp: datetime = Field(..., description="Timestamp of accident occurrence (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude")
    h3_cell: str = Field(..., description="Uber H3 spatial index cell (res 8 default)")
    severity: int = Field(default=2, ge=1, le=4, description="Accident severity score (1-4)")
    source: str = Field(default="kaggle_us_accidents", description="Source data feed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw source metadata and flags")

    @field_validator("h3_cell")
    @classmethod
    def validate_h3_cell(cls, v: str) -> str:
        if not v or len(v) < 15:
            raise ValueError(f"Invalid H3 cell index format: {v}")
        return v.strip().lower()


class NegativeSample(BaseModel):
    """Synthetically generated non-accident (negative) sample for class-balanced spatio-temporal training."""
    id: str = Field(..., description="Deterministic synthetic identifier (e.g., neg_{accident_id}_{offset})")
    accident_ref_id: str = Field(..., description="Source positive accident event ID")
    timestamp: datetime = Field(..., description="Offset timestamp (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    h3_cell: str = Field(..., description="Same H3 cell as source positive event")
    label: int = Field(default=0, description="Binary classification label (0=non-accident)")
    time_offset_hours: int = Field(..., description="Hour offset applied from parent accident")


class EnrichedSample(BaseModel):
    """Spatio-temporal sample enriched with async NOAA/Open-Meteo weather and calculated solar metrics."""
    id: str = Field(..., description="Record ID")
    is_accident: bool = Field(..., description="True if accident (1), False if negative sample (0)")
    timestamp: datetime = Field(..., description="Event timestamp (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    h3_cell: str = Field(..., description="Uber H3 cell index")
    
    # Weather metrics
    temperature_c: float = Field(..., description="Ambient temperature in Celsius")
    precipitation_mm: float = Field(default=0.0, ge=0.0, description="Precipitation rate mm/h")
    wind_speed_kmh: float = Field(default=0.0, ge=0.0, description="Wind speed km/h")
    visibility_km: float = Field(default=10.0, ge=0.0, description="Atmospheric visibility km")
    humidity_pct: float = Field(default=50.0, ge=0.0, le=100.0, description="Relative humidity %")
    weather_condition: str = Field(default="Clear", description="Categorical weather state")

    # Solar position & glare metrics
    solar_elevation_deg: float = Field(..., ge=-90.0, le=90.0, description="Sun elevation angle above horizon")
    solar_azimuth_deg: float = Field(..., ge=0.0, le=360.0, description="Sun azimuth angle (degrees from North)")
    sun_glare_risk: float = Field(default=0.0, ge=0.0, le=1.0, description="Calculated driver sun glare index (0-1)")

    # Optional metadata
    extra_features: Dict[str, Any] = Field(default_factory=dict)
