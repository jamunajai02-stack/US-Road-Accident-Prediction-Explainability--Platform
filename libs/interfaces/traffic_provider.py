"""Abstract base class interface for real-time traffic and incident providers."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from libs.schemas.graph import SubgraphQuery


class TrafficIncident(ABC):
    """Marker interface for traffic incident events."""
    pass


class TrafficProvider(ABC):
    """Interface for obtaining live road traffic speeds, congestion levels, and DOT incident feeds."""

    @abstractmethod
    async def get_live_incidents(self, region_code: str) -> List[Dict[str, Any]]:
        """Fetch current active road incident / workzone records for a state or region."""
        pass

    @abstractmethod
    async def get_traffic_density(
        self, edge_ids: List[str], timestamp_epoch: Optional[int] = None
    ) -> Dict[str, float]:
        """Fetch traffic density index (0.0 to 1.0) for specified road edge IDs.
        
        Args:
            edge_ids: Target road segment IDs
            timestamp_epoch: Target timestamp, or None for latest live reading
            
        Returns:
            Dictionary mapping edge_id -> normalized traffic density (0.0=free flow, 1.0=jam)
        """
        pass

    @abstractmethod
    async def stream_incidents(self, region_code: str) -> AsyncIterator[Dict[str, Any]]:
        """Yield live incident stream events asynchronously."""
        pass
