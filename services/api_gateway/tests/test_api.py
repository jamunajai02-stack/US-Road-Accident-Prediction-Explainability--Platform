"""Integration tests for FastAPI Gateway route functions and container."""

import asyncio
import unittest
from libs.schemas.alert import RouteRequest, Waypoint
from services.api_gateway.dependencies import get_service_container
from services.api_gateway.routes.health import health_check, get_metrics
from services.api_gateway.routes.predict import predict_corridor_risk
from services.api_gateway.routes.route_check import check_route_safety
from services.api_gateway.routes.hotspots import list_active_hotspots, get_hotspot_explanation


class TestAPIGateway(unittest.TestCase):

    def setUp(self):
        self.container = get_service_container()

    def test_health_and_metrics_endpoints(self):
        async def run_test():
            health = await health_check(self.container)
            self.assertEqual(health["status"], "HEALTHY")
            self.assertIn("graph_nodes", health)

            metrics = await get_metrics(self.container)
            self.assertIn("active_feature_cache", metrics)

        asyncio.run(run_test())

    def test_predict_endpoint(self):
        async def run_test():
            result = await predict_corridor_risk(edge_ids=["1_2_0", "2_3_0"], container=self.container)
            self.assertIsNotNone(result.prediction_id)
            self.assertGreater(result.num_edges_evaluated, 0)
            self.assertGreaterEqual(result.inference_latency_ms, 0.0)

        asyncio.run(run_test())

    def test_route_check_endpoint(self):
        async def run_test():
            req = RouteRequest(
                route_id="api_test_trip",
                origin=Waypoint(latitude=37.7749, longitude=-122.4194),
                destination=Waypoint(latitude=37.7850, longitude=-122.4100),
            )
            resp = await check_route_safety(req, container=self.container)
            self.assertEqual(resp.route_id, "api_test_trip")
            self.assertIn(resp.overall_safety_status, ["SAFE", "CAUTION", "HAZARDOUS"])
            self.assertIsNotNone(resp.recommended_route_geometry)

        asyncio.run(run_test())

    def test_hotspots_and_explanation_endpoints(self):
        async def run_test():
            hotspots = await list_active_hotspots(container=self.container)
            self.assertIsInstance(hotspots, list)

            explanation = await get_hotspot_explanation("hotspot_cluster_1", container=self.container)
            self.assertEqual(explanation.cluster_id, "hotspot_cluster_1")
            self.assertIsNotNone(explanation.summary)
            self.assertIsNotNone(explanation.driver_advisory)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
