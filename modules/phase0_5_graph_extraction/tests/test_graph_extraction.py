"""Unit tests for Phase 0.5 Road Graph Extraction."""

import tempfile
import unittest
from pathlib import Path
from modules.phase0_5_graph_extraction.graph_builder import RoadGraphBuilder
from modules.phase0_5_graph_extraction.pbf_extractor import PBFGraphExtractor


class TestGraphExtraction(unittest.TestCase):

    def setUp(self):
        self.builder = RoadGraphBuilder(h3_resolution=8)

    def test_build_nodes_and_edges(self):
        # Node 1 and Node 2 in San Francisco
        n1 = self.builder.add_node(1, 37.7749, -122.4194)
        n2 = self.builder.add_node(2, 37.7790, -122.4150)
        
        self.assertEqual(n1.node_id, 1)
        self.assertEqual(n2.node_id, 2)
        self.assertEqual(self.builder.graph.number_of_nodes(), 2)

        # Curved connecting edge
        coords = [(37.7749, -122.4194), (37.7770, -122.4180), (37.7790, -122.4150)]
        edge = self.builder.add_edge(
            source_id=1,
            target_id=2,
            osm_way_id=12345,
            coordinates=coords,
            speed_limit_kmh=60.0,
            lanes=2,
            highway_type="primary",
            is_oneway=True,
        )

        self.assertEqual(edge.source_node_id, 1)
        self.assertEqual(edge.target_node_id, 2)
        self.assertGreater(edge.length_meters, 0.0)
        self.assertGreaterEqual(edge.sinuosity, 1.0)
        self.assertGreaterEqual(edge.curvature, 0.0)
        self.assertEqual(self.builder.graph.number_of_edges(), 1)

    def test_save_and_load_graph(self):
        self.builder.add_node(10, 37.7749, -122.4194)
        self.builder.add_node(20, 37.7790, -122.4150)
        self.builder.add_edge(10, 20, osm_way_id=999, is_oneway=False)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "test_graph.json"
            self.builder.save(str(out_file))
            self.assertTrue(out_file.exists())

            loaded_graph = RoadGraphBuilder.load(str(out_file))
            self.assertEqual(loaded_graph.number_of_nodes(), 2)
            # Bidirectional edge -> 2 directed edges
            self.assertEqual(loaded_graph.number_of_edges(), 2)

    def test_sample_grid_graph_generation(self):
        extractor = PBFGraphExtractor(h3_resolution=8)
        builder = RoadGraphBuilder(h3_resolution=8)
        extractor._build_sample_grid_graph(builder)
        
        # 4x4 grid -> 16 nodes
        self.assertEqual(builder.graph.number_of_nodes(), 16)
        # Grid edges in both directions
        self.assertGreater(builder.graph.number_of_edges(), 20)


if __name__ == "__main__":
    unittest.main()
