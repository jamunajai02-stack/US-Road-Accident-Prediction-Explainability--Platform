"""Pydantic schemas for topological road network nodes, edges, curvature features, and subgraphs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RoadNode(BaseModel):
    """Intersection or junction point in the OpenStreetMap road network graph."""
    node_id: int = Field(..., description="OSM node ID or synthetic integer index")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    h3_cell: str = Field(..., description="Uber H3 spatial cell containing node")
    elevation_meters: Optional[float] = Field(default=0.0)


class RoadEdge(BaseModel):
    """Directed road segment carrying topological, geometric, static and dynamic features."""
    edge_id: str = Field(..., description="Unique deterministic edge identifier (e.g., u_v_key)")
    source_node_id: int = Field(..., description="Start node ID")
    target_node_id: int = Field(..., description="End node ID")
    osm_way_id: Optional[int] = Field(default=None, description="Original OSM way ID")
    h3_cell: str = Field(..., description="Primary H3 cell of road segment centroid")
    
    # Topological & Physical Road Features (Patch 5: curvature & sinuosity)
    length_meters: float = Field(..., ge=0.0, description="Segment arc length in meters")
    curvature: float = Field(default=0.0, ge=0.0, description="Road curvature index / turning-angle variance")
    sinuosity: float = Field(default=1.0, ge=1.0, description="Sinuosity ratio = arc length / chord length")
    speed_limit_kmh: float = Field(default=50.0, ge=0.0, description="Design or posted speed limit in km/h")
    lanes: int = Field(default=1, ge=1, le=16, description="Number of directional travel lanes")
    highway_type: str = Field(default="secondary", description="OSM highway classification (motorway, trunk, etc.)")
    is_oneway: bool = Field(default=False)
    is_bridge: bool = Field(default=False)
    is_tunnel: bool = Field(default=False)
    has_divider: bool = Field(default=False)
    
    # Geometry string (WKT)
    geometry_wkt: Optional[str] = Field(default=None, description="Well-Known-Text LineString representation")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphSnapshot(BaseModel):
    """Temporal snapshot of the road graph for a specific 1-hour time frame."""
    snapshot_id: str = Field(..., description="Snapshot identifier (e.g., snap_20230101_1400)")
    timestamp: datetime = Field(..., description="Start timestamp of the 1-hour temporal window (UTC)")
    num_nodes: int = Field(..., ge=1)
    num_edges: int = Field(..., ge=1)
    h3_region: str = Field(..., description="Regional H3 cluster or bounding polygon identifier")
    edge_ids: List[str] = Field(..., description="Ordered list of edge IDs matching adjacency tensor rows")


class SubgraphQuery(BaseModel):
    """Request query to extract a localized road network subgraph around a point of interest."""
    center_latitude: float = Field(..., ge=-90.0, le=90.0)
    center_longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_km: float = Field(default=16.0, ge=1.0, le=100.0, description="Radius in km (default 10 miles ~16 km)")
    timestamp: Optional[datetime] = Field(default=None, description="Target forecast timestamp (UTC)")
