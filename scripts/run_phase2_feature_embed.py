"""CLI script to run Phase 2: Feature Embedding, Edge Snapping & Temporal Alignment."""

import argparse
import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libs.common.config import ConfigLoader
from libs.common.logger import logger
from modules.phase0_5_graph_extraction.graph_builder import RoadGraphBuilder
from modules.phase2_graph_construction.feature_embedding.embedder import GraphFeatureEmbedder
from modules.phase2_graph_construction.temporal_alignment.aligner import TemporalGraphAligner


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2: Feature Embedding & Temporal Alignment")
    parser.add_argument("--graph", type=str, default="data/processed/road_graph_v1.gpkg", help="Path to road graph artifact")
    parser.add_argument("--enriched", type=str, default="data/processed/enriched_samples.parquet", help="Path to Phase 1 enriched parquet")
    parser.add_argument("--output", type=str, default="data/processed/aligned_snapshots.pt", help="Path to output PyG tensor dataset")
    args = parser.parse_args()

    logger.info("Initializing Phase 2 Pipeline", graph_path=args.graph, enriched_path=args.enriched)

    # 1. Load road graph
    if not Path(args.graph).exists():
        logger.info("Road graph not found, building initial baseline graph")
        from modules.phase0_5_graph_extraction.pbf_extractor import PBFGraphExtractor
        extractor = PBFGraphExtractor(h3_resolution=8)
        builder = RoadGraphBuilder(h3_resolution=8)
        extractor._build_sample_grid_graph(builder)
        builder.save(args.graph)
        road_graph = builder.graph
    else:
        road_graph = RoadGraphBuilder.load(args.graph)

    # 2. Load enriched samples
    if not Path(args.enriched).exists():
        logger.warn("Enriched parquet not found, creating synthetic enriched dataframe for demo")
        from datetime import datetime, timezone
        df_records = []
        for u, v, data in road_graph.edges(data=True):
            e_id = data.get("edge_id")
            for h in range(6):
                df_records.append({
                    "id": f"rec_{e_id}_{h}",
                    "is_accident": (h % 3 == 0 and u == 1),
                    "timestamp": datetime(2023, 6, 1, 12 + h, 0, 0, tzinfo=timezone.utc),
                    "latitude": road_graph.nodes[u]["latitude"],
                    "longitude": road_graph.nodes[u]["longitude"],
                    "h3_cell": data.get("h3_cell", "8828308281fffff"),
                    "temperature_c": 22.0 + h,
                    "precipitation_mm": 3.0 if (h % 2 == 1) else 0.0,
                    "wind_speed_kmh": 15.0,
                    "visibility_km": 8.0,
                    "humidity_pct": 65.0,
                    "solar_elevation_deg": 50.0 - (h * 5),
                    "solar_azimuth_deg": 180.0 + (h * 15),
                    "sun_glare_risk": 0.4 if h == 4 else 0.0,
                })
        enriched_df = pd.DataFrame(df_records)
    else:
        enriched_df = pd.read_parquet(args.enriched)

    # 3. Embed features & Snap H3 cells to edges (Patch 1)
    embedder = GraphFeatureEmbedder(road_graph)
    snapped_df = embedder.snap_samples_to_edges(enriched_df)

    # 4. Temporal Alignment (PyG snapshot tensors)
    aligner = TemporalGraphAligner(road_graph)
    snapshots = aligner.build_snapshots(snapped_df, output_pt_path=args.output)

    logger.info(
        "Phase 2 Complete: Spatio-temporal snapshot dataset ready for deep learning core",
        total_snapshots=len(snapshots),
        saved_path=args.output,
    )


if __name__ == "__main__":
    main()
