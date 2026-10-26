"""CLI script to run Phase 1: Spatial Indexing, Negative Sampling & Weather Enrichment."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libs.common.config import ConfigLoader
from libs.common.geo import GeoUtils
from libs.common.logger import logger
from libs.schemas.accident import AccidentEvent
from modules.phase1_data_infra.negative_sampling.sampler import StratifiedNegativeSampler
from modules.phase1_data_infra.spatial_indexing.indexer import SpatialIndexer
from modules.phase1_data_infra.weather_enrichment.enrichment_pipeline import AsyncEnrichmentPipeline
from modules.phase1_data_infra.weather_enrichment.noaa_adapter import NOAAWeatherAdapter
from modules.phase1_data_infra.weather_enrichment.open_meteo_adapter import OpenMeteoWeatherAdapter


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1: Ingestion, Negative Sampling & Enrichment")
    parser.add_argument("--input", type=str, default="archive.zip", help="Path to raw Kaggle zip/csv")
    parser.add_argument("--output", type=str, default="data/processed/enriched_samples.parquet")
    parser.add_argument("--max-records", type=int, default=100, help="Max positive records to process for demo/run")
    parser.add_argument("--provider", type=str, default="open_meteo", choices=["open_meteo", "noaa"])
    parser.add_argument(
        "--bbox",
        type=str,
        default=None,
        help="Optional geographic filter 'min_lat,min_lng,max_lat,max_lng' to keep accidents near the road graph region",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        default=False,
        help="Use offline static weather features (no NOAA/Open-Meteo HTTP calls) for reproducible local training",
    )
    args = parser.parse_args()

    bbox = None
    if args.bbox:
        parts = [float(x) for x in args.bbox.split(",")]
        if len(parts) == 4:
            bbox = {"min_lat": parts[0], "min_lng": parts[1], "max_lat": parts[2], "max_lng": parts[3]}
        else:
            logger.warn("Invalid --bbox; ignoring geographic filter", raw=args.bbox)

    cfg = ConfigLoader.load("base")
    h3_cfg = ConfigLoader.load("h3_grid")
    thresholds_cfg = ConfigLoader.load("thresholds")

    logger.info("Initializing Phase 1 Pipeline", max_records=args.max_records, provider=args.provider)

    # 1. Spatial indexing
    indexer = SpatialIndexer(h3_resolution=h3_cfg["h3"]["resolution"])
    positive_events = []
    
    if Path(args.input).exists():
        input_path = Path(args.input)
        if str(input_path).lower().endswith(".csv"):
            # Fast vectorized path: selective columns + vectorized bbox filter +
            # vectorized timestamp parsing (avoids slow per-row pandas operations
            # on the multi-GB Kaggle CSV).
            import pandas as pd

            usecols = ["ID", "Severity", "Start_Time", "Start_Lat", "Start_Lng", "Source"]
            dtypes = {"ID": "str", "Severity": "int8", "Start_Lat": "float32", "Start_Lng": "float32", "Source": "str"}
            reader = pd.read_csv(
                input_path,
                usecols=usecols,
                dtype=dtypes,
                chunksize=250000,
                low_memory=False,
            )
            for chunk in reader:
                chunk = chunk.dropna(subset=["Start_Lat", "Start_Lng"])
                if bbox:
                    chunk = chunk[
                        (chunk["Start_Lat"].between(bbox["min_lat"], bbox["max_lat"]))
                        & (chunk["Start_Lng"].between(bbox["min_lng"], bbox["max_lng"]))
                    ]
                if chunk.empty:
                    continue
                times = pd.to_datetime(chunk["Start_Time"], errors="coerce", utc=True)
                chunk = chunk.assign(_ts=times).dropna(subset=["_ts"])
                if chunk.empty:
                    continue
                for _, r in chunk.iterrows():
                    lat = float(r["Start_Lat"])
                    lon = float(r["Start_Lng"])
                    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                        continue
                    positive_events.append(AccidentEvent(
                        id=str(r["ID"]) if pd.notna(r["ID"]) else f"acc_{len(positive_events)}",
                        timestamp=r["_ts"].to_pydatetime(),
                        latitude=lat,
                        longitude=lon,
                        h3_cell=GeoUtils.lat_lng_to_h3(lat, lon, h3_cfg["h3"]["resolution"]),
                        severity=max(1, min(4, int(r["Severity"]))) if pd.notna(r["Severity"]) else 2,
                        source=str(r["Source"]) if pd.notna(r["Source"]) else "kaggle",
                    ))
                    if len(positive_events) >= args.max_records:
                        break
                if len(positive_events) >= args.max_records:
                    break
        else:
            stream_max = None if bbox else args.max_records
            for chunk in indexer.parse_csv_stream(str(input_path), chunk_size=50000, max_records=stream_max):
                if bbox:
                    chunk = [
                        evt
                        for evt in chunk
                        if bbox["min_lat"] <= evt.latitude <= bbox["max_lat"]
                        and bbox["min_lng"] <= evt.longitude <= bbox["max_lng"]
                    ]
                positive_events.extend(chunk)
                if len(positive_events) >= args.max_records:
                    break
    else:
        logger.warn("Input dataset file not found, generating sample accident events", input_path=args.input)
        from datetime import datetime, timezone
        for i in range(args.max_records):
            positive_events.append(
                AccidentEvent(
                    id=f"acc_synth_{i}",
                    timestamp=datetime(2023, 3, 15, 17, 30, 0, tzinfo=timezone.utc),
                    latitude=37.7749 + (i % 4) * 0.008,
                    longitude=-122.4194 + (i // 4) * 0.008,
                    h3_cell=GeoUtils.lat_lng_to_h3(37.7749 + (i % 4) * 0.008, -122.4194 + (i // 4) * 0.008),
                    severity=3 if i % 3 == 0 else 2,
                )
            )

    logger.info("Spatial indexing complete", total_positives=len(positive_events))

    # 2. Stratified negative sampling
    ratio = thresholds_cfg["thresholds"]["negative_sampling"]["ratio"]
    sampler = StratifiedNegativeSampler(sampling_ratio=ratio)
    negative_samples = sampler.generate_negatives(positive_events)

    all_samples = positive_events + negative_samples
    logger.info("Negative sampling complete", total_combined_samples=len(all_samples))

    # 3. Weather & solar enrichment
    if args.no_network:
        from modules.phase1_data_infra.weather_enrichment.enrichment_pipeline import StaticWeatherProvider
        weather_provider = StaticWeatherProvider()
        logger.info("Using offline static weather features (--no-network)")
    elif args.provider == "noaa":
        weather_provider = NOAAWeatherAdapter(rate_limit_rps=5)
    else:
        weather_provider = OpenMeteoWeatherAdapter(rate_limit_rps=10)

    enricher = AsyncEnrichmentPipeline(
        weather_provider=weather_provider,
        checkpoint_dir=cfg["storage"]["checkpoints_dir"],
        batch_size=50,
    )

    saved_parquet = await enricher.enrich_samples(
        samples=all_samples,
        output_parquet_path=args.output,
        resume=True,
    )
    logger.info("Phase 1 Complete: Enriched dataset generated", output_path=saved_parquet)


if __name__ == "__main__":
    asyncio.run(async_main())
