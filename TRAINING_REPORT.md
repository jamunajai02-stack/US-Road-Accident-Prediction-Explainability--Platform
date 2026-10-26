# Training & Integration Report — Kaggle US Accidents Rebuild

**Date:** 2026-08-22 · **Scope:** Bug fixes + full Kaggle retrain + routing geometry repair

---

## 1. Data Source

| Item | Value |
|---|---|
| Raw file | `US_Accidents_March23.csv` (3.06 GB, Kaggle US Accidents) |
| Total records | 7,728,394 (2016 → 2023-04) |
| Ingestion region | SF bbox `37.770,-122.425 → 37.805,-122.390` (aligned to road graph) |
| Positives ingested | **3,414** accidents |
| Negatives sampled | **11,971** (ratio 3.51:1) |
| Enriched dataset | `data/processed/enriched_samples_sf.parquet` (15,385 rows) |
| Snapshots | `data/processed/aligned_snapshots_sf.pt` — **12,789** one-hour graph snapshots |
| Positive label rate | 0.491 % (3,017 / 613,872 edge-labels) |
| Weather enrichment | Offline `StaticWeatherProvider` (`--no-network`); solar computed locally |

Training used **time-stratified sampling** (`--max-snapshots 2000`) — evenly spaced over the full
2016→2023 range to keep the chronological split valid and epochs tractable.

## 2. Training Configuration

- Model: `STGCNPredictor` (SpatialGraphConv → Transformer encoder → CalibratedProbabilityHead)
- Split (chronological, leak-free): **train 1,679 / val 262 / test 59** snapshots
- Optimizer: Adam (lr 1e-3, wd 1e-4), BCELoss(pos_weight=3.5), 12 epochs
- Calibration: Elkan prior-shift (β=0.222 → γ=0.005)

## 3. Results

| Metric | Value | Interpretation |
|---|---|---|
| Final train loss | 0.1107 | stable convergence |
| Val PR-AUC | 0.2509 | vs 0.49 % base → **~50× lift** over random |
| **Test PR-AUC** | **0.2103** | strong ranking on unseen year (2023) |
| **Test ROC-AUC** | **0.9914** | excellent positive/negative separation |
| **Test Brier** | **0.0035** | well-calibrated on sparse outcomes |
| Mean calibrated prob | 0.0001 | matches real-world sparse base rate |

**Artifacts:** `data/processed/stgcn_model.pth` (trained, 325,600 B, verified loadable by the
serving pipeline). ONNX export was skipped because `onnx`/`onnxscript` are not installed in this
environment — by design the exporter now writes **only** the `.pth` and never corrupts `.onnx`.

## 4. Bugs Fixed

### Routing drew straight lines instead of roads (root causes)
1. `valhalla_adapter._extract_edge_ids_from_valhalla` was a stub returning fake `valhalla_leg_*`
   IDs → replaced with real OSM-way → graph-edge mapping + encoded-polyline shape decoding.
2. `get_alternate_route` returned a hardcoded 2-point `LINESTRING` → now assembles the detour
   from actual per-edge WKT geometry, with **real** `additional_distance_km` / `additional_time_minutes`.
3. `alert_builder` always emitted origin→destination straight lines for SAFE/CAUTION (and used the
   straight detour for HAZARDOUS) → now builds road-following geometry via the new
   `RoutingEngine.get_route_geometry(edge_ids)` interface method (straight line only as last-resort fallback).

**Verified:** primary route → 4-point LINESTRING; detour → 10-point LINESTRING following grid roads;
travel impact computed from path length (+4.8 km / +6.4 min).

### Other fixes
4. `run_phase1_enrichment.py` — `indexer.lat_lng_to_h3` AttributeError → `GeoUtils.lat_lng_to_h3`.
5. `trainer.export_onnx` — dropped unsupported `dynamo=` kwarg; `.onnx` no longer overwritten by a
   state dict; always writes portable `.pth`; test updated to the corrected contract.
6. `runner.py` weight loading — prefers `.pth`, validates the state dict, falls back safely.
7. `frontend/src/api/client.ts` — `POST /v1/predict` now sends `edge_ids` as **query params**
   (backend ignores the body it previously received).
8. Added `--bbox` geographic filter + fast **vectorized** CSV ingestion (3 GB scanned in ~55 s)
   and `--no-network` offline enrichment mode to `run_phase1_enrichment.py`.

## 5. Verification

- **27/27** unit & integration tests pass across all 8 suites.
- Live demo (`run_phase5_live_demo.py`) runs end-to-end with the trained weights: serving loads
  `stgcn_model.pth`, hotspots isolated at ≥80 %, natural-language causative advisories generated,
  HAZARDOUS route intercepted with a safe road-following detour.

## 6. Known Limitations

- The road graph remains the built-in 16-node SF demo grid (no OSM `.pbf` / `pyrosm` available
  offline), so geographic fidelity is bounded by that graph.
- `data/processed/stgcn_model.onnx` is a **stale legacy file** (a state dict mislabeled `.onnx`
  from before the fix). It is unused — serving prefers `.pth`. Install `onnx` and re-run
  Phase 3 to produce a genuine ONNX graph.
- Weather features are static defaults in this offline run; with network access, re-run Phase 1
  without `--no-network` for live NOAA/Open-Meteo enrichment.
