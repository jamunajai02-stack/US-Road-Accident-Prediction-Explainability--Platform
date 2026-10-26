"""Topological road graph constructor and serializer."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx
from libs.common.geo import GeoUtils
from libs.common.logger import logger
from libs.schemas.graph import RoadEdge, RoadNode


class RoadGraphBuilder:
    """Constructs directed NetworkX graphs from road segment records and computes topology features."""

    def __init__(self, h3_resolution: int = 8):
        self.h3_resolution = h3_resolution
        self.graph = nx.DiGraph()

    def add_node(self, node_id: int, latitude: float, longitude: float, elevation: float = 0.0) -> RoadNode:
        """Add a junction node to the graph."""
        h3_cell = GeoUtils.lat_lng_to_h3(latitude, longitude, self.h3_resolution)
        node = RoadNode(
            node_id=node_id,
            latitude=latitude,
            longitude=longitude,
            h3_cell=h3_cell,
            elevation_meters=elevation,
        )
        self.graph.add_node(
            node_id,
            latitude=latitude,
            longitude=longitude,
            h3_cell=h3_cell,
            elevation=elevation,
        )
        return node

    def add_edge(
        self,
        source_id: int,
        target_id: int,
        osm_way_id: Optional[int] = None,
        coordinates: Optional[List[Tuple[float, float]]] = None,
        speed_limit_kmh: float = 50.0,
        lanes: int = 1,
        highway_type: str = "secondary",
        is_oneway: bool = False,
        is_bridge: bool = False,
        is_tunnel: bool = False,
    ) -> RoadEdge:
        """Add a directed road edge connecting two nodes, calculating geometry and curvature."""
        edge_id = f"{source_id}_{target_id}_{osm_way_id or 0}"

        if not coordinates:
            # Fallback to straight line connecting source and target nodes
            src_lat = self.graph.nodes[source_id]["latitude"]
            src_lon = self.graph.nodes[source_id]["longitude"]
            tgt_lat = self.graph.nodes[target_id]["latitude"]
            tgt_lon = self.graph.nodes[target_id]["longitude"]
            coordinates = [(src_lat, src_lon), (tgt_lat, tgt_lon)]

        # Calculate geometric physical attributes (Patch 5: curvature & sinuosity)
        length_meters, sinuosity = GeoUtils.calculate_sinuosity(coordinates)
        curvature_var = GeoUtils.calculate_turning_angle_variance(coordinates)

        # Centroid coordinate for H3 indexing
        mid_idx = len(coordinates) // 2
        centroid_lat, centroid_lon = coordinates[mid_idx]
        h3_cell = GeoUtils.lat_lng_to_h3(centroid_lat, centroid_lon, self.h3_resolution)

        # Well-Known Text geometry representation
        wkt_points = ", ".join(f"{lon} {lat}" for lat, lon in coordinates)
        wkt_geom = f"LINESTRING ({wkt_points})"

        edge = RoadEdge(
            edge_id=edge_id,
            source_node_id=source_id,
            target_node_id=target_id,
            osm_way_id=osm_way_id,
            h3_cell=h3_cell,
            length_meters=max(1.0, length_meters),
            curvature=curvature_var,
            sinuosity=sinuosity,
            speed_limit_kmh=speed_limit_kmh,
            lanes=max(1, lanes),
            highway_type=highway_type,
            is_oneway=is_oneway,
            is_bridge=is_bridge,
            is_tunnel=is_tunnel,
            geometry_wkt=wkt_geom,
        )

        self.graph.add_edge(
            source_id,
            target_id,
            key=edge_id,
            **edge.model_dump(),
        )

        if not is_oneway:
            # Add reverse edge for bi-directional streets
            rev_edge_id = f"{target_id}_{source_id}_{osm_way_id or 0}"
            rev_coords = list(reversed(coordinates))
            rev_edge = RoadEdge(
                edge_id=rev_edge_id,
                source_node_id=target_id,
                target_node_id=source_id,
                osm_way_id=osm_way_id,
                h3_cell=h3_cell,
                length_meters=max(1.0, length_meters),
                curvature=curvature_var,
                sinuosity=sinuosity,
                speed_limit_kmh=speed_limit_kmh,
                lanes=max(1, lanes),
                highway_type=highway_type,
                is_oneway=is_oneway,
                is_bridge=is_bridge,
                is_tunnel=is_tunnel,
                geometry_wkt=wkt_geom,
            )
            self.graph.add_edge(
                target_id,
                source_id,
                key=rev_edge_id,
                **rev_edge.model_dump(),
            )

        return edge

    def save(self, output_path: str) -> str:
        """Persist graph structure and features to file (GraphML / JSON)."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize node-link data
        data = nx.node_link_data(self.graph)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            
        logger.info(
            "Road graph saved successfully",
            path=str(path),
            nodes=self.graph.number_of_nodes(),
            edges=self.graph.number_of_edges(),
        )
        return str(path)

    @classmethod
    def load(cls, input_path: str) -> nx.DiGraph:
        """Load graph from serialized file."""
        path = Path(input_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return nx.node_link_graph(data, directed=True)
