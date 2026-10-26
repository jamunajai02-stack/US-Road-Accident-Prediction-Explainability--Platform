"""CLI script to build and serialize the static versioned road graph artifact."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libs.common.config import ConfigLoader
from libs.common.logger import logger
from modules.phase0_5_graph_extraction.pbf_extractor import PBFGraphExtractor


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 0.5: Road Graph Extraction & Serialization")
    parser.add_argument("--pbf-path", type=str, default=None, help="Path to Geofabrik .pbf file (optional)")
    parser.add_argument("--output", type=str, default=None, help="Destination path for graph artifact")
    args = parser.parse_args()

    cfg = ConfigLoader.load("base")
    h3_cfg = ConfigLoader.load("h3_grid")
    
    output_path = args.output or cfg["storage"]["road_graph_path"]
    resolution = h3_cfg["h3"]["resolution"]

    logger.info("Starting Phase 0.5 Road Graph Extraction", output=output_path, h3_res=resolution)
    extractor = PBFGraphExtractor(h3_resolution=resolution)

    if args.pbf_path and Path(args.pbf_path).exists():
        saved_path = extractor.extract_from_pbf(args.pbf_path, output_path)
    else:
        # Build synthetic regional road corridor graph as baseline
        from modules.phase0_5_graph_extraction.graph_builder import RoadGraphBuilder
        builder = RoadGraphBuilder(h3_resolution=resolution)
        extractor._build_sample_grid_graph(builder)
        saved_path = builder.save(output_path)

    logger.info("Phase 0.5 Complete: Road graph artifact generated", saved_path=saved_path)


if __name__ == "__main__":
    main()
