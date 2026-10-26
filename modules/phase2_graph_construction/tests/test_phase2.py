"""Unit tests for Phase 2 Feature Embedding & Temporal Alignment."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import torch
from modules.phase0_5_graph_extraction.graph_builder import RoadGraphBuilder
from modules.phase2_graph_construction.feature_embedding.embedder import GraphFeatureEmbedder
from modules.phase2_graph_construction.temporal_alignment.aligner import TemporalGraphAligner


class TestPhase2GraphConstruction(unittest.TestCase):

    def setUp(self):
        self.builder = RoadGraphBuilder(h3_resolution=8)
        # Create a small 3-node connected road triangle
        self.builder.add_node(1, 37.7749, -122.4194)
        self.builder.add_node(2, 37.7790, -122.4150)
        self.builder.add_node(3, 37.7720, -122.4120)

        coords_12 = [(37.7749, -122.4194), (37.7770, -122.4170), (37.7790, -122.4150)]
        self.builder.add_edge(1, 2, osm_way_id=101, coordinates=coords_12, is_oneway=True, speed_limit_kmh=65.0)
        self.builder.add_edge(2, 3, osm_way_id=102, is_oneway=True, speed_limit_kmh=45.0)
        self.builder.add_edge(3, 1, osm_way_id=103, is_oneway=True, speed_limit_kmh=50.0)

        self.graph = self.builder.graph

    def test_static_feature_embedding_shape_and_curvature(self):
        embedder = GraphFeatureEmbedder(self.graph)
        edge_ids, feat_matrix = embedder.extract_static_edge_features()

        self.assertEqual(len(edge_ids), 3)
        self.assertEqual(feat_matrix.shape, (3, 10))
        
        # Check first edge curvature and sinuosity columns (indices 1 and 2)
        self.assertGreater(feat_matrix[0, 2], 0.0)  # sinuosity
        self.assertGreaterEqual(feat_matrix[0, 1], 0.0)  # curvature

    def test_temporal_snapshot_alignment(self):
        aligner = TemporalGraphAligner(self.graph)
        
        # Synthetic enriched dataframe across 2 different 1-hour windows
        t1 = datetime(2023, 6, 1, 14, 15, 0, tzinfo=timezone.utc)
        t2 = datetime(2023, 6, 1, 15, 45, 0, tzinfo=timezone.utc)
        
        df_records = [
            {
                "id": "acc_1",
                "is_accident": True,
                "timestamp": t1,
                "latitude": 37.7749,
                "longitude": -122.4194,
                "h3_cell": "8828308281fffff",
                "temperature_c": 19.0,
                "precipitation_mm": 5.0,
                "wind_speed_kmh": 20.0,
                "visibility_km": 6.0,
                "humidity_pct": 80.0,
                "solar_elevation_deg": 45.0,
                "solar_azimuth_deg": 210.0,
                "sun_glare_risk": 0.2,
                "edge_id": "1_2_101",
            },
            {
                "id": "neg_1",
                "is_accident": False,
                "timestamp": t2,
                "latitude": 37.7790,
                "longitude": -122.4150,
                "h3_cell": "8828308281fffff",
                "temperature_c": 22.0,
                "precipitation_mm": 0.0,
                "wind_speed_kmh": 10.0,
                "visibility_km": 10.0,
                "humidity_pct": 50.0,
                "solar_elevation_deg": 35.0,
                "solar_azimuth_deg": 230.0,
                "sun_glare_risk": 0.0,
                "edge_id": "2_3_102",
            },
        ]
        df = pd.DataFrame(df_records)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "snapshots.pt"
            snapshots = aligner.build_snapshots(df, output_pt_path=str(out_file))

            self.assertEqual(len(snapshots), 2)
            snap0 = snapshots[0]

            # Verify PyG tensor formats
            self.assertEqual(snap0["x"].shape, (3, 2))  # 3 nodes, lat/lon
            self.assertEqual(snap0["edge_index"].shape, (2, 3))  # 3 directed edges
            self.assertEqual(snap0["edge_attr"].shape, (3, 18))  # 10 static + 8 dynamic = 18 features
            self.assertEqual(snap0["y"].shape, (3, 1))  # 3 edge labels
            self.assertEqual(snap0["y"][0].item(), 1.0)  # Edge 1_2_101 had positive accident


if __name__ == "__main__":
    unittest.main()
