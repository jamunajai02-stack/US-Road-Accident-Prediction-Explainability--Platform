"""Pydantic schemas for weather observations, forecasts, and astronomical solar metrics."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class WeatherCondition(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    FOG = "fog"
    THUNDERSTORM = "thunderstorm"
    HAIL = "hail"
    UNKNOWN = "unknown"


class SolarMetrics(BaseModel):
    """Astronomical solar positioning parameters calculated for driver glare estimation."""
    elevation_deg: float = Field(..., ge=-90.0, le=90.0, description="Sun elevation angle above horizon")
    azimuth_deg: float = Field(..., ge=0.0, le=360.0, description="Sun azimuth clockwise from true North")
    is_daylight: bool = Field(..., description="True if sun elevation > 0 degrees")
    glare_risk: float = Field(default=0.0, ge=0.0, le=1.0, description="Estimated glare risk factor (0 to 1)")


class WeatherSnapshot(BaseModel):
    """Standardized weather record returned by NOAA, Open-Meteo, or live stream adapters."""
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: datetime = Field(..., description="Observation or forecast timestamp in UTC")
    temperature_c: float = Field(..., description="Air temperature in Celsius")
    precipitation_mm: float = Field(default=0.0, ge=0.0, description="Precipitation rate mm/hour")
    wind_speed_kmh: float = Field(default=0.0, ge=0.0, description="Wind speed in km/h")
    wind_direction_deg: float = Field(default=0.0, ge=0.0, le=360.0, description="Wind direction clockwise from North")
    visibility_km: float = Field(default=10.0, ge=0.0, description="Visibility distance in km")
    humidity_pct: float = Field(default=50.0, ge=0.0, le=100.0, description="Relative humidity percentage")
    pressure_hpa: Optional[float] = Field(default=1013.25, description="Surface barometric pressure in hPa")
    condition: WeatherCondition = Field(default=WeatherCondition.CLEAR)
    source_provider: str = Field(default="noaa", description="Provider identifier (noaa, open_meteo, etc.)")
