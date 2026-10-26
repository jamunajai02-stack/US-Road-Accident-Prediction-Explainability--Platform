"""Open-Meteo historical and live weather provider adapter."""

import asyncio
from datetime import datetime, timezone
from typing import List, Tuple
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from libs.common.exceptions import WeatherProviderError
from libs.common.logger import logger
from libs.interfaces.weather_provider import WeatherProvider
from libs.schemas.weather import WeatherCondition, WeatherSnapshot


class OpenMeteoWeatherAdapter(WeatherProvider):
    """Adapter for Open-Meteo historical archive API and live forecast API."""

    def __init__(
        self,
        archive_base_url: str = "https://archive-api.open-meteo.com/v1/archive",
        forecast_base_url: str = "https://api.open-meteo.com/v1/forecast",
        rate_limit_rps: int = 10,
        timeout_seconds: int = 10,
    ):
        self.archive_base_url = archive_base_url
        self.forecast_base_url = forecast_base_url
        self.semaphore = asyncio.Semaphore(rate_limit_rps)
        self.timeout = timeout_seconds

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
    async def get_weather(
        self, latitude: float, longitude: float, timestamp: datetime
    ) -> WeatherSnapshot:
        """Fetch historical weather observation for a coordinate and timestamp."""
        async with self.semaphore:
            date_str = timestamp.strftime("%Y-%m-%d")
            hour_idx = timestamp.hour

            params = {
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "start_date": date_str,
                "end_date": date_str,
                "hourly": "temperature_2m,relative_humidity_2m,precipitation,visibility,wind_speed_10m,wind_direction_10m,weather_code",
                "timezone": "UTC",
            }

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(self.archive_base_url, params=params)
                    if resp.status_code != 200:
                        # Fallback to forecast API if date is recent
                        resp = await client.get(self.forecast_base_url, params=params)
                    
                    if resp.status_code != 200:
                        raise WeatherProviderError(f"Open-Meteo returned status {resp.status_code}")

                    data = resp.json()
                    hourly = data.get("hourly", {})
                    
                    # Safe extraction with defaults
                    def get_hour_val(field: str, default: float) -> float:
                        arr = hourly.get(field, [])
                        if arr and len(arr) > hour_idx and arr[hour_idx] is not None:
                            return float(arr[hour_idx])
                        return default

                    temp_c = get_hour_val("temperature_2m", 20.0)
                    humidity = get_hour_val("relative_humidity_2m", 50.0)
                    precip = get_hour_val("precipitation", 0.0)
                    vis_m = get_hour_val("visibility", 10000.0)
                    wind_speed = get_hour_val("wind_speed_10m", 10.0)
                    wind_dir = get_hour_val("wind_direction_10m", 180.0)
                    wcode = int(get_hour_val("weather_code", 0))

                    # Map WMO weather code to WeatherCondition
                    cond = WeatherCondition.CLEAR
                    if wcode in (1, 2, 3):
                        cond = WeatherCondition.CLOUDY
                    elif wcode in (45, 48):
                        cond = WeatherCondition.FOG
                    elif wcode in (51, 53, 55, 61, 63):
                        cond = WeatherCondition.RAIN
                    elif wcode in (65, 66, 67, 80, 81, 82):
                        cond = WeatherCondition.HEAVY_RAIN
                    elif wcode in (71, 73, 75, 85, 86):
                        cond = WeatherCondition.SNOW
                    elif wcode in (95, 96, 99):
                        cond = WeatherCondition.THUNDERSTORM

                    return WeatherSnapshot(
                        latitude=latitude,
                        longitude=longitude,
                        timestamp=timestamp,
                        temperature_c=temp_c,
                        precipitation_mm=precip,
                        wind_speed_kmh=wind_speed,
                        wind_direction_deg=wind_dir,
                        visibility_km=vis_m / 1000.0,
                        humidity_pct=humidity,
                        condition=cond,
                        source_provider="open_meteo",
                    )
            except Exception as e:
                raise WeatherProviderError(f"Open-Meteo query failed for ({latitude}, {longitude}): {e}") from e

    async def batch_get_weather(
        self, points: List[Tuple[float, float, datetime]]
    ) -> List[WeatherSnapshot]:
        """Fetch multiple observations concurrently."""
        tasks = [self.get_weather(lat, lon, dt) for lat, lon, dt in points]
        return await asyncio.gather(*tasks, return_exceptions=False)
