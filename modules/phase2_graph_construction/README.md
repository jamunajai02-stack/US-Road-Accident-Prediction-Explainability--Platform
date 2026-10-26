# Phase 2: Topological Graph Construction & Feature Alignment

## Purpose
Constructs rich spatio-temporal road graph representations by:
1. Embedding static physical edge attributes (speed limits, lanes, one-way flags, curvature, sinuosity).
2. Performing spatial joins snapping enriched accident/non-accident samples from H3 bins to corresponding road graph edges (`h3_cell -> edge_id`).
3. Slicing dynamic continuous states into rolling 1-hour temporal snapshots formatted as PyTorch Geometric (PyG) compatible tensors.

## Architecture & Principles
- **Separation of Concerns**:
  - `feature_embedding/`: Manages static edge feature extraction and H3-to-edge spatial snapping (Patch 1 & Patch 5).
  - `temporal_alignment/`: Bins edge-snapped observations into discrete 1-hour snapshots `(x, edge_index, edge_attr, y)` ready for Phase 3 deep learning consumption.

## Inputs & Outputs
- **Inputs**:
  - Road graph artifact: `data/processed/road_graph_v1.gpkg` (from Phase 0.5)
  - Enriched dataset: `data/processed/enriched_samples.parquet` (from Phase 1)
- **Output**:
  - Aligned PyTorch tensor dataset: `data/processed/aligned_snapshots.pt`

## Standalone Usage
```bash
python scripts/run_phase2_feature_embed.py --graph data/processed/road_graph_v1.gpkg --enriched data/processed/enriched_samples.parquet
```
