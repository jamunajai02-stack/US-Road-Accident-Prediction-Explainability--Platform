# Phase 1: Data Infrastructure & Enrichment

## Purpose
Ingests raw Kaggle US Accidents records, indexes events into Uber H3 spatial cells (res 8), dynamically generates stratified negative (non-accident) samples at the exact same location, and enriches all space-time points with async NOAA/Open-Meteo weather and computed astronomical solar position & driver glare metrics.

## Architecture & Principles
- **Separation of Concerns**:
  - `spatial_indexing/`: H3 spatial cell assignment only. **Road snapping is strictly deferred to Phase 2 (Patch 1)**.
  - `negative_sampling/`: Stratified time offset generation (day-of-week, hour shifts) with positive accident collision avoidance.
  - `weather_enrichment/`: `WeatherProvider` interface implementations (`NOAAWeatherAdapter`, `OpenMeteoWeatherAdapter`) and `AsyncEnrichmentPipeline` with semaphore rate-limiting and parquet checkpointing.

## Inputs & Outputs
- **Input**: Raw Kaggle dataset (`archive.zip` / `US_Accidents_March23.csv`).
- **Output**: Enriched versioned dataset `data/processed/enriched_samples.parquet`.

## Configuration Keys
- `configs/base.yaml`: `providers.weather`, `storage.interim_data_dir`, `storage.processed_data_dir`.
- `configs/h3_grid.yaml`: `h3.resolution`.
- `configs/thresholds.yaml`: `thresholds.negative_sampling.ratio`, `thresholds.negative_sampling.time_offset_days`.

## Standalone Usage
```bash
python scripts/run_phase1_enrichment.py --input archive.zip --max-records 1000
```
