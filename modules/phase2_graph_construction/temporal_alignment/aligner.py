"""Temporal alignment module constructing rolling 1-hour spatio-temporal PyG graph tensors."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx
import numpy as np
import pandas as pd
import torch
from libs.common.logger import logger
from modules.phase2_graph_construction.feature_embedding.embedder import GraphFeatureEmbedder


class TemporalGraphAligner:
    """Aligns static road graph structure and dynamic snapped features into 1-hour PyG snapshot tensors."""

    def __init__(self, road_graph: nx.DiGraph):
        self.road_graph = road_graph
        self.embedder = GraphFeatureEmbedder(road_graph)
        self.node_id_to_idx: Dict[int, int] = {}
        self.edge_id_to_idx: Dict[str, int] = {}
        self.edge_index: torch.Tensor = torch.empty((2, 0), dtype=torch.long)
        self.static_edge_features: torch.Tensor = torch.empty((0, 10), dtype=torch.float32)
        self._build_graph_tensors()

    def _build_graph_tensors(self) -> None:
        """Construct adjacency index and static edge feature tensors."""
        # Map node IDs to continuous 0-indexed integers
        sorted_nodes = sorted(self.road_graph.nodes())
        self.node_id_to_idx = {nid: idx for idx, nid in enumerate(sorted_nodes)}

        # Edge index & static feature matrix
        src_indices = []
        tgt_indices = []
        edge_ids, static_feats = self.embedder.extract_static_edge_features()

        for idx, (u, v, data) in enumerate(self.road_graph.edges(data=True)):
            edge_id = data.get("edge_id") or f"{u}_{v}_0"
            self.edge_id_to_idx[edge_id] = idx
            src_indices.append(self.node_id_to_idx[u])
            tgt_indices.append(self.node_id_to_idx[v])

        self.edge_index = torch.tensor([src_indices, tgt_indices], dtype=torch.long)
        self.static_edge_features = torch.from_numpy(static_feats)

    def build_snapshots(
        self,
        snapped_df: pd.DataFrame,
        output_pt_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Slice dataframe into 1-hour windows and build aligned PyG-compatible tensor dictionaries."""
        df = snapped_df.copy()
        if "timestamp" not in df.columns:
            raise ValueError("Dataframe must contain 'timestamp' column")

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour_bucket"] = df["timestamp"].dt.floor("1h")

        unique_hours = sorted(df["hour_bucket"].unique())
        logger.info("Aligning temporal snapshots", num_1hr_windows=len(unique_hours), num_edges=len(self.edge_id_to_idx))

        num_nodes = len(self.node_id_to_idx)
        num_edges = len(self.edge_id_to_idx)
        snapshots: List[Dict[str, Any]] = []

        for hr in unique_hours:
            hr_df = df[df["hour_bucket"] == hr]
            
            # Dynamic feature vector per edge (8 dynamic features)
            dynamic_edge_feats = np.zeros((num_edges, 8), dtype=np.float32)
            dynamic_edge_feats[:, 0] = 20.0 / 50.0   # temp norm
            dynamic_edge_feats[:, 3] = 10.0 / 10.0   # visibility norm
            dynamic_edge_feats[:, 4] = 0.50          # humidity norm

            # Ground-truth accident labels per edge for this hour
            y_labels = np.zeros((num_edges, 1), dtype=np.float32)

            for _, row in hr_df.iterrows():
                e_id = row.get("edge_id")
                if e_id in self.edge_id_to_idx:
                    idx = self.edge_id_to_idx[e_id]
                    
                    # Update dynamic features
                    temp_norm = float(row.get("temperature_c", 20.0)) / 50.0
                    precip = float(row.get("precipitation_mm", 0.0))
                    wind_norm = min(1.0, float(row.get("wind_speed_kmh", 10.0)) / 100.0)
                    vis_norm = min(1.0, float(row.get("visibility_km", 10.0)) / 10.0)
                    humid_norm = float(row.get("humidity_pct", 50.0)) / 100.0
                    solar_elev = (float(row.get("solar_elevation_deg", 0.0)) + 90.0) / 180.0
                    glare = float(row.get("sun_glare_risk", 0.0))
                    traffic_density = float(row.get("traffic_density", 0.20))

                    dynamic_edge_feats[idx] = [
                        temp_norm,
                        precip,
                        wind_norm,
                        vis_norm,
                        humid_norm,
                        solar_elev,
                        glare,
                        traffic_density,
                    ]

                    if bool(row.get("is_accident", False)):
                        y_labels[idx] = 1.0

            # Combined edge features: (E, 10 static + 8 dynamic = 18 channels)
            combined_edge_attr = torch.cat(
                [self.static_edge_features, torch.from_numpy(dynamic_edge_feats)], dim=1
            )

            # Node features: spatial coordinates
            node_coords = np.zeros((num_nodes, 2), dtype=np.float32)
            for nid, idx in self.node_id_to_idx.items():
                node_coords[idx, 0] = self.road_graph.nodes[nid]["latitude"]
                node_coords[idx, 1] = self.road_graph.nodes[nid]["longitude"]

            snapshot_dict = {
                "timestamp": hr.to_pydatetime(),
                "x": torch.from_numpy(node_coords),
                "edge_index": self.edge_index,
                "edge_attr": combined_edge_attr,
                "y": torch.from_numpy(y_labels),
                "num_nodes": num_nodes,
                "num_edges": num_edges,
                "edge_ids": list(self.edge_id_to_idx.keys()),
            }
            snapshots.append(snapshot_dict)

        if output_pt_path:
            out_file = Path(output_pt_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            torch.save(snapshots, out_file)
            logger.info("Saved aligned graph snapshot dataset", path=str(out_file), snapshots_count=len(snapshots))

        return snapshots
