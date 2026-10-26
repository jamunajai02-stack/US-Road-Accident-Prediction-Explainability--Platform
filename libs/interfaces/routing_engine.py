"""Abstract base class interface for vehicle navigation and detour routing engines."""

from abc import ABC, abstractmethod
from typing import List, Optional
from libs.schemas.alert import DetourOption, RouteRequest, Waypoint


class RoutingEngine(ABC):
    """Interface for querying turn-by-turn routing engines (Valhalla / OSRM)."""

    @abstractmethod
    async def calculate_route(
        self, origin: Waypoint, destination: Waypoint, waypoints: Optional[List[Waypoint]] = None
    ) -> List[str]:
        """Compute the primary route and return ordered road edge IDs or coordinate pairs."""
        pass

    @abstractmethod
    async def get_alternate_route(
        self,
        origin: Waypoint,
        destination: Waypoint,
        avoid_edge_ids: List[str],
        primary_route_risk: float,
    ) -> DetourOption:
        """Compute an alternative safe detour that explicitly avoids hazardous hotspot road edges.
        
        Args:
            origin: Trip starting point
            destination: Trip destination
            avoid_edge_ids: Hazardous road edge IDs to penalize / avoid
            primary_route_risk: Baseline risk of original path
            
        Returns:
            DetourOption schema containing safe polyline and calculated risk reduction
        """
        pass

    def get_route_geometry(self, edge_ids: List[str]) -> str:
        """Return a road-following WKT LINESTRING geometry for an ordered list of edge IDs.

        Optional capability: adapters that cannot resolve per-edge geometry should
        return an empty string, in which case callers fall back to a straight line.
        """
        return ""
