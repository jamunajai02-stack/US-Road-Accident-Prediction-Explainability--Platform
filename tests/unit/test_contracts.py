"""Unit tests for Phase 0 contracts, schemas, interfaces, and common utilities."""

import unittest
from datetime import datetime, timezone
from libs.schemas.accident import AccidentEvent, EnrichedSample, NegativeSample
from libs.schemas.weather import SolarMetrics, WeatherCondition, WeatherSnapshot
from libs.schemas.graph import GraphSnapshot, RoadEdge, RoadNode, SubgraphQuery
from libs.schemas.prediction import EdgeRiskPrediction, ProbabilityOutput, RiskBand
from libs.schemas.explanation import DecisionRule, HotspotCluster, HotspotRule, NaturalLanguageExplanation
from libs.schemas.alert import AlertPayload, DetourOption, RouteRequest, RouteResponse, Waypoint
from libs.common.config import ConfigLoader
from libs.common.solar import SolarEngine
from libs.common.geo import GeoUtils


class TestPhase0Contracts(unittest.TestCase):

    def test_accident_event_schema_validation(self):
        h3_idx = GeoUtils.lat_lng_to_h3(37.7749, -122.4194, resolution=8)
        event = AccidentEvent(
            id="acc_001",
            timestamp=datetime.now(timezone.utc),
            latitude=37.7749,
            longitude=-122.4194,
            h3_cell=h3_idx,
            severity=3,
        )
        self.assertEqual(event.id, "acc_001")
        self.assertEqual(event.h3_cell, h3_idx)

    def test_road_edge_schema_with_curvature(self):
        edge = RoadEdge(
            edge_id="node1_node2_0",
            source_node_id=1,
            target_node_id=2,
            h3_cell="8828308281fffff",
            length_meters=450.5,
            curvature=12.4,
            sinuosity=1.15,
            speed_limit_kmh=65.0,
            lanes=2,
            highway_type="primary",
        )
        self.assertEqual(edge.curvature, 12.4)
        self.assertEqual(edge.sinuosity, 1.15)

    def test_probability_output_calibration_schema(self):
        prob = ProbabilityOutput(
            raw_probability=0.85,
            calibrated_probability=0.72,
            probability_percentage=72.0,
            calibration_method="elkan_log_odds",
        )
        self.assertEqual(prob.calibrated_probability, 0.72)

    def test_solar_engine_azimuth_elevation(self):
        dt = datetime(2023, 6, 21, 19, 0, 0, tzinfo=timezone.utc)
        metrics = SolarEngine.calculate_solar_position(37.7749, -122.4194, dt)
        self.assertIsInstance(metrics, SolarMetrics)
        self.assertTrue(-90.0 <= metrics.elevation_deg <= 90.0)
        self.assertTrue(0.0 <= metrics.azimuth_deg <= 360.0)

    def test_geo_utils_bearing_sinuosity(self):
        coords = [(37.7749, -122.4194), (37.7755, -122.4180), (37.7760, -122.4170)]
        arc_len, sinuosity = GeoUtils.calculate_sinuosity(coords)
        self.assertGreater(arc_len, 0)
        self.assertGreaterEqual(sinuosity, 1.0)

    def test_config_loader(self):
        ConfigLoader.clear_cache()
        base_cfg = ConfigLoader.load("base")
        self.assertEqual(base_cfg["app"]["name"], "accident-prediction-platform")
        self.assertEqual(base_cfg["providers"]["weather"]["primary"], "noaa")


if __name__ == "__main__":
    unittest.main()
