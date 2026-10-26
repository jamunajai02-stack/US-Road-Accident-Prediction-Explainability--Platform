"""Abstract base class interface for road network graph storage and spatial queries."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import networkx as nx
from libs.schemas.graph import RoadEdge, RoadNode, SubgraphQuery


class GraphStore(ABC):
    """Interface for querying and persisting the topological road network (PostGIS / GeoPackage)."""

    @abstractmethod
    def load_graph(self) -> nx.DiGraph:
        """Load entire road network graph into memory as a directed NetworkX graph."""
        pass

    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional[RoadEdge]:
        """Fetch static road edge attributes by edge ID."""
        pass

    @abstractmethod
    def query_subgraph(self, query: SubgraphQuery) -> nx.DiGraph:
        """Extract a localized spatial subgraph within the specified radius around a coordinate."""
        pass

    @abstractmethod
    def persist_graph(self, graph: nx.DiGraph, version_tag: str) -> str:
        """Persist graph structure and features to durable storage (GeoPackage / PostGIS)."""
        pass
