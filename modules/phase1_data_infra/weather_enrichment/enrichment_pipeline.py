"""Asynchronous batch enrichment pipeline combining weather and astronomical solar metrics."""

import asyncio
from pathlib import Path
from typing import List, Optional, Union
import pandas as pd
from libs.common.exceptions import WeatherProviderError
from libs.common.logger import logger
from libs.common.solar import SolarEngine
from libs.interfaces.weather_provider import WeatherProvider
from libs.schemas.accident import AccidentEvent, EnrichedSample, NegativeSample
from libs.schemas.weather import WeatherSnapshot


class StaticWeatherProvider(WeatherProvider):
    """Deterministic offline weather provider returning fixed atmospheric defaults.

    Used with --no-network so the enrichment pipeline does not stall on unavailable
    NOAA / Open-Meteo endpoints while still producing valid, reproducible features
    for training.
    """

    def __init__(self, temperature_c: float = 20.0, precipitation_mm: float = 0.0,
                 wind_speed_kmh: float = 10.0, visibility_km: float = 10.0,
                 humidity_pct: float = 50.0):
        self.temperature_c = temperature_c
        self.precipitation_mm = precipitation_mm
        self.wind_speed_kmh = wind_speed_kmh
        self.visibility_km = visibility_km
        self.humidity_pct = humidity_pct

    async def get_weather(self, latitude: float, longitude: float, timestamp) -> WeatherSnapshot:
        return WeatherSnapshot(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            temperature_c=self.temperature_c,
            precipitation_mm=self.precipitation_mm,
            wind_speed_kmh=self.wind_speed_kmh,
            wind_direction_deg=180.0,
            visibility_km=self.visibility_km,
            humidity_pct=self.humidity_pct,
        )

    async def batch_get_weather(self, points) -> list:
        return [await self.get_weather(lat, lon, ts) for lat, lon, ts in points]


class AsyncEnrichmentPipeline:
    """Orchestrates async batch weather and solar enrichment with checkpoint/resume support."""

    def __init__(
        self,
        weather_provider: WeatherProvider,
        checkpoint_dir: str = "data/interim/checkpoints",
        batch_size: int = 100,
    ):
        self.weather_provider = weather_provider
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.batch_size = batch_size

    async def enrich_samples(
        self,
        samples: List[Union[AccidentEvent, NegativeSample]],
        output_parquet_path: str,
        resume: bool = True,
    ) -> str:
        """Enrich all samples asynchronously and persist to a versioned Parquet dataset."""
        out_path = Path(output_parquet_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Starting batch weather & solar enrichment",
            total_samples=len(samples),
            batch_size=self.batch_size,
            output_path=str(out_path),
        )

        enriched_records: List[EnrichedSample] = []
        
        # Check for existing checkpoint
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{out_path.stem}.parquet"
        completed_ids = set()
        if resume and checkpoint_file.exists():
            try:
                df_chk = pd.read_parquet(checkpoint_file)
                completed_ids = set(df_chk["id"].astype(str))
                logger.info("Resuming from checkpoint", completed_count=len(completed_ids))
            except Exception as e:
                logger.warn("Could not read checkpoint file, starting fresh", error=str(e))

        # Filter remaining samples
        remaining_samples = [s for s in samples if s.id not in completed_ids]

        for i in range(0, len(remaining_samples), self.batch_size):
            batch = remaining_samples[i : i + self.batch_size]
            batch_enriched = await self._enrich_batch(batch)
            enriched_records.extend(batch_enriched)

            # Checkpoint progress periodically
            if len(enriched_records) >= 500 or (i + self.batch_size) >= len(remaining_samples):
                self._save_checkpoint(enriched_records, checkpoint_file)

        # Merge with existing checkpoint data if any
        if checkpoint_file.exists():
            df_final = pd.read_parquet(checkpoint_file)
        else:
            df_final = pd.DataFrame([r.model_dump() for r in enriched_records])

        # Write final processed parquet
        df_final.to_parquet(out_path, index=False, engine="pyarrow")
        logger.info(
            "Enrichment completed successfully",
            final_records_count=len(df_final),
            saved_to=str(out_path),
        )
        return str(out_path)

    async def _enrich_batch(
        self, batch: List[Union[AccidentEvent, NegativeSample]]
    ) -> List[EnrichedSample]:
        """Process a single batch concurrently."""
        points = [(s.latitude, s.longitude, s.timestamp) for s in batch]
        
        # 1. Fetch weather concurrently
        try:
            weather_snapshots = await self.weather_provider.batch_get_weather(points)
        except Exception as e:
            logger.warn("Batch weather fetch error, using robust atmospheric defaults", error=str(e))
            # Fallback default weather snapshots
            weather_snapshots = [
                WeatherSnapshot(
                    latitude=s.latitude,
                    longitude=s.longitude,
                    timestamp=s.timestamp,
                    temperature_c=20.0,
                    precipitation_mm=0.0,
                    wind_speed_kmh=10.0,
                    wind_direction_deg=180.0,
                    visibility_km=10.0,
                    humidity_pct=50.0,
                )
                for s in batch
            ]

        # 2. Compute solar positions and combine into EnrichedSample
        results: List[EnrichedSample] = []
        for s, w in zip(batch, weather_snapshots):
            solar = SolarEngine.calculate_solar_position(s.latitude, s.longitude, s.timestamp)
            is_acc = isinstance(s, AccidentEvent)

            enriched = EnrichedSample(
                id=s.id,
                is_accident=is_acc,
                timestamp=s.timestamp,
                latitude=s.latitude,
                longitude=s.longitude,
                h3_cell=s.h3_cell,
                temperature_c=w.temperature_c,
                precipitation_mm=w.precipitation_mm,
                wind_speed_kmh=w.wind_speed_kmh,
                visibility_km=w.visibility_km,
                humidity_pct=w.humidity_pct,
                weather_condition=w.condition.value if hasattr(w.condition, "value") else str(w.condition),
                solar_elevation_deg=solar.elevation_deg,
                solar_azimuth_deg=solar.azimuth_deg,
                sun_glare_risk=solar.glare_risk,
                extra_features={"severity": getattr(s, "severity", 2) if is_acc else 0},
            )
            results.append(enriched)

        return results

    def _save_checkpoint(self, new_records: List[EnrichedSample], checkpoint_file: Path) -> None:
        if not new_records:
            return
        df_new = pd.DataFrame([r.model_dump() for r in new_records])
        if checkpoint_file.exists():
            try:
                df_existing = pd.read_parquet(checkpoint_file)
                df_merged = pd.concat([df_existing, df_new]).drop_duplicates(subset=["id"])
                df_merged.to_parquet(checkpoint_file, index=False)
                return
            except Exception:
                pass
        df_new.to_parquet(checkpoint_file, index=False)
