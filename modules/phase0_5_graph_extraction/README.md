# Phase 0.5: Shared OSM Road Graph Extraction

## Purpose
Extracts topological road network graphs (nodes and directed edges) from offline Geofabrik `.pbf` extracts, calculating geometric curvature, sinuosity, and lane attributes, and serializing a static versioned road graph artifact (`data/processed/road_graph_v1.gpkg` / `.json`).

## Architecture & Responsibilities
- **`pbf_extractor.py`**: Offline processing of regional OpenStreetMap `.pbf` files filtering for drivable highways.
- **`graph_builder.py`**: Builds directed `NetworkX.DiGraph`, attaches H3 cell spatial indices, derives turning-angle curvature variance and sinuosity ratios.
- **`overpass_debug.py`**: Gated debug adapter for ad-hoc localized queries on small bounding boxes without rate-limiting production pipelines.

## Inputs & Outputs
- **Input**: Geofabrik `.pbf` extract or synthetic road network configuration.
- **Output**: Versioned road graph file (`data/processed/road_graph_v1.json` / `.gpkg`) containing `RoadNode` and `RoadEdge` schemas.

## Configuration Keys
- `h3.resolution`: Spatial resolution for edge centroid assignment (default 8).
- `storage.road_graph_path`: Output artifact destination.

## Standalone Usage
```bash
python scripts/run_phase0_5_graph_build.py --output data/processed/road_graph_v1.json
```
