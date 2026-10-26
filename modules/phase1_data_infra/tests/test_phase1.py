"""Unit tests for Phase 1 Data Infrastructure & Enrichment with mocked weather providers."""

import asyncio
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from libs.interfaces.weather_provider import WeatherProvider
from libs.schemas.accident import AccidentEvent
from libs.schemas.weather import WeatherCondition, WeatherSnapshot
from modules.phase1_data_infra.negative_sampling.sampler import StratifiedNegativeSampler
from modules.phase1_data_infra.spatial_indexing.indexer import SpatialIndexer
from modules.phase1_data_infra.weather_enrichment.enrichment_pipeline import AsyncEnrichmentPipeline


class MockWeatherProvider(WeatherProvider):
    """Mock weather provider returning deterministic atmospheric readings."""

    async def get_weather(self, latitude: float, longitude: float, timestamp: datetime) -> WeatherSnapshot:
        return WeatherSnapshot(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            temperature_c=18.5,
            precipitation_mm=2.5,
            wind_speed_kmh=15.0,
            wind_direction_deg=220.0,
            visibility_km=8.0,
            humidity_pct=75.0,
            condition=WeatherCondition.RAIN,
            source_provider="mock_noaa",
        )

    async def batch_get_weather(self, points):
        return [await self.get_weather(lat, lon, ts) for lat, lon, ts in points]


class TestPhase1DataInfra(unittest.TestCase):

    def setUp(self):
        self.indexer = SpatialIndexer(h3_resolution=8)
        self.sampler = StratifiedNegativeSampler(sampling_ratio=3.5, seed=123)
        self.mock_provider = MockWeatherProvider()

    def test_stratified_negative_sampling_ratio(self):
        base_time = datetime(2023, 5, 10, 14, 0, 0, tzinfo=timezone.utc)
        positives = [
            AccidentEvent(
                id=f"acc_{i}",
                timestamp=base_time,
                latitude=37.7749 + (i * 0.01),
                longitude=-122.4194 + (i * 0.01),
                h3_cell=f"8828308281ffff{i}",
                severity=2,
            )
            for i in range(10)
        ]

        negatives = self.sampler.generate_negatives(positives)
        
        # With 3.5 ratio, 10 positives should yield ~35 negatives
        self.assertTrue(30 <= len(negatives) <= 40)
        for neg in negatives:
            self.assertEqual(neg.label, 0)
            self.assertIn("neg_acc_", neg.id)
            self.assertNotEqual(neg.timestamp, base_time)

    def test_async_weather_and_solar_enrichment_pipeline(self):
        async def run_pipeline():
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_path = Path(tmp_dir) / "enriched_test.parquet"
                chk_dir = Path(tmp_dir) / "checkpoints"

                pipeline = AsyncEnrichmentPipeline(
                    weather_provider=self.mock_provider,
                    checkpoint_dir=str(chk_dir),
                    batch_size=5,
                )

                events = [
                    AccidentEvent(
                        id=f"acc_enrich_{i}",
                        timestamp=datetime(2023, 6, 21, 16, 0, 0, tzinfo=timezone.utc),
                        latitude=37.7749,
                        longitude=-122.4194,
                        h3_cell="8828308281fffff",
                        severity=3,
                    )
                    for i in range(5)
                ]

                result_path = await pipeline.enrich_samples(events, str(out_path), resume=False)
                self.assertTrue(Path(result_path).exists())

                import pandas as pd
                df = pd.read_parquet(result_path)
                self.assertEqual(len(df), 5)
                self.assertIn("precipitation_mm", df.columns)
                self.assertIn("solar_elevation_deg", df.columns)
                self.assertIn("sun_glare_risk", df.columns)
                self.assertEqual(df["precipitation_mm"].iloc[0], 2.5)

        asyncio.run(run_pipeline())


if __name__ == "__main__":
    unittest.main()
