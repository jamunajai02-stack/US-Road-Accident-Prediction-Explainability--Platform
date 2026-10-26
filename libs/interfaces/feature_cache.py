"""Abstract interface for real-time edge dynamic feature cache (Patch 6)."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class FeatureCache(ABC):
    """Interface for low-latency in-memory / Redis feature store supporting sub-10ms inference."""

    @abstractmethod
    async def get_edge_state(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve latest dynamic feature state for an edge (weather, traffic, glare)."""
        pass

    @abstractmethod
    async def bulk_get_edge_states(self, edge_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Bulk fetch latest dynamic features for multiple edges."""
        pass

    @abstractmethod
    async def set_edge_state(self, edge_id: str, features: Dict[str, Any], ttl_seconds: int = 3600) -> None:
        """Update or insert dynamic feature state for an edge with TTL."""
        pass

    @abstractmethod
    async def bulk_set_edge_states(self, updates: Dict[str, Dict[str, Any]], ttl_seconds: int = 3600) -> None:
        """Batch update dynamic feature states across multiple edges."""
        pass
