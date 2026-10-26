"""CLI script to run Phase 4: Localized Hotspot Isolation & Natural Language Explainability."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libs.common.config import ConfigLoader
from libs.common.logger import logger
from libs.schemas.prediction import EdgeRiskPrediction, RiskBand
from modules.phase0_5_graph_extraction.graph_builder import RoadGraphBuilder
from modules.phase4_explainability.hotspot_isolation.isolator import HotspotIsolator
from modules.phase4_explainability.rule_miner.miner import FEATURE_NAMES, LocalizedRuleMiner
from modules.phase4_explainability.rule_translator.translator import RuleTranslator


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4: Hotspot Isolation & Explainability")
    parser.add_argument("--graph", type=str, default="data/processed/road_graph_v1.gpkg")
    parser.add_argument("--threshold", type=float, default=0.80)
    args = parser.parse_args()

    thresholds_cfg = ConfigLoader.load("thresholds")
    cutoff = args.threshold or thresholds_cfg["thresholds"]["hotspot"]["probability_cutoff"]

    logger.info("Initializing Phase 4 Explainability Engine", cutoff=cutoff)

    # 1. Load road graph
    if not Path(args.graph).exists():
        from modules.phase0_5_graph_extraction.pbf_extractor import PBFGraphExtractor
        extractor = PBFGraphExtractor(h3_resolution=8)
        builder = RoadGraphBuilder(h3_resolution=8)
        extractor._build_sample_grid_graph(builder)
        builder.save(args.graph)
        road_graph = builder.graph
    else:
        road_graph = RoadGraphBuilder.load(args.graph)

    # 2. Generate simulated predictions with a high hazard corridor
    now = datetime.now(timezone.utc)
    predictions = []
    for idx, (u, v, data) in enumerate(road_graph.edges(data=True)):
        e_id = data.get("edge_id") or f"{u}_{v}_0"
        # Simulate hotspot on primary highway edges
        is_high = (u in (1, 2) and v in (2, 3, 5, 6))
        risk = 0.86 if is_high else (0.10 + (idx % 4) * 0.12)
        band = RiskBand.SEVERE if risk >= cutoff else RiskBand.LOW
        predictions.append(EdgeRiskPrediction(
            edge_id=e_id,
            timestamp=now,
            risk_score=risk,
            risk_band=band,
            is_hotspot=(risk >= cutoff),
        ))

    # 3. Hotspot Isolation
    isolator = HotspotIsolator(probability_threshold=cutoff, cluster_min_size=1)
    clusters = isolator.isolate_hotspots(predictions, road_graph)

    # 4. Rule Mining & Translation per hotspot cluster
    miner = LocalizedRuleMiner(max_depth=3)
    translator = RuleTranslator()

    print("\n" + "=" * 80)
    print("PHASE 4: LOCALIZED HOTSPOT EXPLAINABILITY REPORT")
    print("=" * 80)

    for cluster in clusters:
        # Simulate localized contextual feature vectors
        np.random.seed(10)
        X = np.random.rand(30, len(FEATURE_NAMES))
        # High precipitation and curvature drive class 1
        X[:, 0] = X[:, 0] * 10.0  # precipitation mm
        X[:, 5] = X[:, 5] * 25.0  # curvature variance
        y = ((X[:, 0] > 4.0) & (X[:, 5] > 8.0)).astype(int)

        rules = miner.mine_rules(cluster, X, y, feature_names=FEATURE_NAMES)
        top_rule = rules[0]
        cluster.top_rule = top_rule

        explanation = translator.translate(cluster, top_rule)

        print(f"\n[HOTSPOT CLUSTER: {cluster.cluster_id}]")
        print(f" • Centroid: ({cluster.centroid_latitude}, {cluster.centroid_longitude})")
        print(f" • Max Risk Score: {round(cluster.max_risk_probability * 100, 1)}%")
        print(f" • Affected Segments: {len(cluster.edge_ids)} road edges")
        print(f" • Headline: {explanation.summary}")
        print(f" • Causative Statement: {explanation.causative_statement}")
        print(f" • Key Factors: {', '.join(explanation.contributing_factors)}")
        print(f" • Driver Advisory: {explanation.driver_advisory}")
        print("-" * 80)

    logger.info("Phase 4 Complete: Hotspot explanations generated", clusters_explained=len(clusters))


if __name__ == "__main__":
    main()
