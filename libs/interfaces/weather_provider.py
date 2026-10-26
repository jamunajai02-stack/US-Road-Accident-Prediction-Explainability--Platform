"""Abstract base class interface for weather observation and forecast providers."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple
from libs.schemas.weather import WeatherSnapshot


class WeatherProvider(ABC):
    """Interface for obtaining historical or real-time atmospheric weather data."""

    @abstractmethod
    async def get_weather(
        self, latitude: float, longitude: float, timestamp: datetime
    ) -> WeatherSnapshot:
        """Fetch weather observation or forecast for a single point in space and time.
        
        Args:
            latitude: WGS84 latitude
            longitude: WGS84 longitude
            timestamp: Observation timestamp (UTC)
            
        Returns:
            WeatherSnapshot normalized schema
        """
        pass

    @abstractmethod
    async def batch_get_weather(
        self, points: List[Tuple[float, float, datetime]]
    ) -> List[WeatherSnapshot]:
        """Asynchronously batch fetch weather observations for multiple space-time coordinates.
        
        Args:
            points: List of (latitude, longitude, timestamp) tuples
            
        Returns:
            List of WeatherSnapshot records matching the input order
        """
        pass
