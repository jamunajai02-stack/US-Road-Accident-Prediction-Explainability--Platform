"""NOAA NWS API weather provider adapter."""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Tuple
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from libs.common.exceptions import WeatherProviderError
from libs.common.logger import logger
from libs.interfaces.weather_provider import WeatherProvider
from libs.schemas.weather import WeatherCondition, WeatherSnapshot


class NOAAWeatherAdapter(WeatherProvider):
    """Adapter for fetching observational weather data from the NOAA National Weather Service API."""

    def __init__(
        self,
        base_url: str = "https://api.weather.gov",
        user_agent: str = "US-Accident-Prediction-Platform/1.0",
        rate_limit_rps: int = 5,
        timeout_seconds: int = 10,
    ):
        self.base_url = base_url
        self.headers = {"User-Agent": user_agent, "Accept": "application/geo+json"}
        self.semaphore = asyncio.Semaphore(rate_limit_rps)
        self.timeout = timeout_seconds

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
    async def get_weather(
        self, latitude: float, longitude: float, timestamp: datetime
    ) -> WeatherSnapshot:
        """Fetch closest station weather from NOAA NWS API."""
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                    # 1. Resolve points to grid metadata
                    point_url = f"{self.base_url}/points/{round(latitude, 4)},{round(longitude, 4)}"
                    resp = await client.get(point_url)
                    if resp.status_code != 200:
                        raise WeatherProviderError(f"NOAA points lookup failed with status {resp.status_code}")

                    grid_data = resp.json()
                    stations_url = grid_data.get("properties", {}).get("observationStations")
                    if not stations_url:
                        raise WeatherProviderError("No NOAA observation stations found for coordinate")

                    # 2. Get closest station observations
                    st_resp = await client.get(stations_url)
                    st_data = st_resp.json()
                    features = st_data.get("features", [])
                    if not features:
                        raise WeatherProviderError("No station features in NOAA response")

                    station_id = features[0]["properties"]["stationIdentifier"]
                    obs_url = f"{self.base_url}/stations/{station_id}/observations/latest"
                    obs_resp = await client.get(obs_url)
                    obs_data = obs_resp.json().get("properties", {})

                    # Extract measurements
                    temp_c = (obs_data.get("temperature", {}) or {}).get("value") or 20.0
                    wind_speed = (obs_data.get("windSpeed", {}) or {}).get("value") or 10.0
                    wind_dir = (obs_data.get("windDirection", {}) or {}).get("value") or 180.0
                    precip = (obs_data.get("precipitationLastHour", {}) or {}).get("value") or 0.0
                    visibility_m = (obs_data.get("visibility", {}) or {}).get("value") or 10000.0
                    humidity = (obs_data.get("relativeHumidity", {}) or {}).get("value") or 50.0

                    return WeatherSnapshot(
                        latitude=latitude,
                        longitude=longitude,
                        timestamp=timestamp,
                        temperature_c=float(temp_c),
                        precipitation_mm=float(precip),
                        wind_speed_kmh=float(wind_speed),
                        wind_direction_deg=float(wind_dir),
                        visibility_km=float(visibility_m) / 1000.0,
                        humidity_pct=float(humidity),
                        condition=WeatherCondition.CLEAR if precip == 0 else WeatherCondition.RAIN,
                        source_provider="noaa",
                    )
            except Exception as e:
                raise WeatherProviderError(f"NOAA API error for ({latitude}, {longitude}): {e}") from e

    async def batch_get_weather(
        self, points: List[Tuple[float, float, datetime]]
    ) -> List[WeatherSnapshot]:
        """Fetch weather concurrently across multiple space-time points."""
        tasks = [self.get_weather(lat, lon, dt) for lat, lon, dt in points]
        return await asyncio.gather(*tasks, return_exceptions=False)
