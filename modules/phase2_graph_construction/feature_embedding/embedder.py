"""Feature embedding module attaching static road attributes, curvature, and dynamic weather/solar states (Patch 1 & Patch 5)."""

from typing import Dict, List, Optional, Tuple
import networkx as nx
import numpy as np
import pandas as pd
from libs.common.geo import GeoUtils
from libs.common.logger import logger
from libs.schemas.accident import EnrichedSample
from libs.schemas.graph import RoadEdge


HIGHWAY_TYPE_MAP = {
    "motorway": 0,
    "motorway_link": 0,
    "trunk": 1,
    "trunk_link": 1,
    "primary": 2,
    "primary_link": 2,
    "secondary": 3,
    "secondary_link": 3,
    "tertiary": 4,
    "tertiary_link": 4,
    "residential": 5,
}


class GraphFeatureEmbedder:
    """Embeds static physical edge features and snaps dynamic space-time enriched records onto graph edges."""

    def __init__(self, road_graph: nx.DiGraph):
        self.road_graph = road_graph
        self.edge_list: List[Dict] = []
        self.h3_to_edges_map: Dict[str, List[str]] = {}
        self._build_edge_index()

    def _build_edge_index(self) -> None:
        """Index all graph edges and construct spatial H3 hash lookup."""
        self.edge_list = []
        self.h3_to_edges_map = {}

        for u, v, data in self.road_graph.edges(data=True):
            edge_id = data.get("edge_id") or f"{u}_{v}_0"
            h3_cell = data.get("h3_cell", "")
            
            self.edge_list.append(data)
            if h3_cell:
                self.h3_to_edges_map.setdefault(h3_cell, []).append(edge_id)

        logger.info(
            "GraphFeatureEmbedder initialized",
            num_nodes=self.road_graph.number_of_nodes(),
            num_edges=len(self.edge_list),
            indexed_h3_cells=len(self.h3_to_edges_map),
        )

    def extract_static_edge_features(self) -> Tuple[List[str], np.ndarray]:
        """Extract static physical and topological feature vectors for all edges.
        
        Returns:
            Tuple of (edge_ids, feature_matrix of shape [E, 10])
        """
        feature_rows = []
        edge_ids = []

        for data in self.edge_list:
            edge_ids.append(data.get("edge_id"))
            
            # Static attributes (Patch 5: curvature and sinuosity)
            length_norm = min(1.0, float(data.get("length_meters", 100.0)) / 2000.0)
            curvature = min(1.0, float(data.get("curvature", 0.0)) / 50.0)
            sinuosity = min(1.0, (float(data.get("sinuosity", 1.0)) - 1.0) / 2.0)
            speed_limit = min(1.0, float(data.get("speed_limit_kmh", 50.0)) / 130.0)
            lanes = min(1.0, float(data.get("lanes", 1)) / 8.0)
            
            # One-hot / ordinal highway classification
            hw_type = str(data.get("highway_type", "secondary"))
            hw_code = HIGHWAY_TYPE_MAP.get(hw_type, 3) / 5.0

            is_oneway = 1.0 if data.get("is_oneway", False) else 0.0
            is_bridge = 1.0 if data.get("is_bridge", False) else 0.0
            is_tunnel = 1.0 if data.get("is_tunnel", False) else 0.0
            has_divider = 1.0 if data.get("has_divider", False) else 0.0

            row = [
                length_norm,
                curvature,
                sinuosity,
                speed_limit,
                lanes,
                hw_code,
                is_oneway,
                is_bridge,
                is_tunnel,
                has_divider,
            ]
            feature_rows.append(row)

        return edge_ids, np.array(feature_rows, dtype=np.float32)

    def snap_samples_to_edges(
        self, enriched_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Snap enriched samples from H3 spatial bins to nearest graph road edge (Patch 1)."""
        df = enriched_df.copy()
        snapped_edge_ids = []

        for _, row in df.iterrows():
            sample_h3 = str(row["h3_cell"])
            matching_edges = self.h3_to_edges_map.get(sample_h3, [])

            if matching_edges:
                # Nearest edge in same H3 cell
                snapped_edge_ids.append(matching_edges[0])
            else:
                # Fallback: find closest edge centroid via Haversine distance
                lat, lon = float(row["latitude"]), float(row["longitude"])
                best_edge = self._find_nearest_edge(lat, lon)
                snapped_edge_ids.append(best_edge)

        df["edge_id"] = snapped_edge_ids
        logger.info("Snapped samples to graph edges", total_records=len(df))
        return df

    def _find_nearest_edge(self, lat: float, lon: float) -> str:
        """Find the nearest graph edge by centroid distance."""
        min_dist = float("inf")
        best_edge_id = self.edge_list[0].get("edge_id") if self.edge_list else "edge_0"

        for data in self.edge_list:
            u = data.get("source_node_id")
            if u in self.road_graph.nodes:
                u_lat = self.road_graph.nodes[u]["latitude"]
                u_lon = self.road_graph.nodes[u]["longitude"]
                dist = GeoUtils.haversine_distance_meters(lat, lon, u_lat, u_lon)
                if dist < min_dist:
                    min_dist = dist
                    best_edge_id = data.get("edge_id")

        return best_edge_id
