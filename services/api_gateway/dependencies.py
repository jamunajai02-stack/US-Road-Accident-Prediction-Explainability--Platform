"""Composition root and dependency injection container for API Gateway services."""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from libs.common.config import ConfigLoader
from libs.common.logger import logger
from modules.phase0_5_graph_extraction.graph_builder import RoadGraphBuilder
from modules.phase4_explainability.hotspot_isolation.isolator import HotspotIsolator
from modules.phase4_explainability.rule_miner.miner import LocalizedRuleMiner
from modules.phase4_explainability.rule_translator.translator import RuleTranslator
from modules.phase5_realtime_service.feature_cache.cache import InMemoryLRUFeatureCache, RedisFeatureCache
from modules.phase5_realtime_service.inference_pipeline.runner import RealTimeInferencePipeline
from modules.phase5_realtime_service.routing_alerts.alert_builder import RouteAlertEngine
from modules.phase5_realtime_service.routing_alerts.valhalla_adapter import ValhallaRoutingAdapter


class ServiceContainer:
    """Dependency Injection container wiring all domain interfaces to concrete implementations."""

    def __init__(self) -> None:
        self.base_cfg = ConfigLoader.load("base")
        self.thresholds_cfg = ConfigLoader.load("thresholds")
        
        # 1. Feature Cache
        cache_backend = self.base_cfg["providers"]["cache"]["backend"]
        if cache_backend == "redis":
            self.feature_cache = RedisFeatureCache(
                redis_url=self.base_cfg["providers"]["cache"]["redis_url"],
                default_ttl_seconds=self.base_cfg["providers"]["cache"]["ttl_seconds"],
            )
        else:
            self.feature_cache = InMemoryLRUFeatureCache()

        # 2. Road Graph Store
        graph_path = self.base_cfg["storage"]["road_graph_path"]
        if Path(graph_path).exists():
            self.road_graph = RoadGraphBuilder.load(graph_path)
        else:
            from modules.phase0_5_graph_extraction.pbf_extractor import PBFGraphExtractor
            extractor = PBFGraphExtractor(h3_resolution=8)
            builder = RoadGraphBuilder(h3_resolution=8)
            extractor._build_sample_grid_graph(builder)
            builder.save(graph_path)
            self.road_graph = builder.graph

        # 3. Real-Time Inference Pipeline
        cutoff = float(self.thresholds_cfg["thresholds"]["hotspot"]["probability_cutoff"])
        self.inference_pipeline = RealTimeInferencePipeline(
            road_graph=self.road_graph,
            feature_cache=self.feature_cache,
            model_path=self.base_cfg["storage"].get("stgcn_onnx_path"),
            probability_cutoff=cutoff,
        )

        # 4. Explainability & Hotspot Isolation
        self.hotspot_isolator = HotspotIsolator(probability_threshold=cutoff)
        self.rule_miner = LocalizedRuleMiner()
        self.rule_translator = RuleTranslator()

        # 5. Routing Engine & Alert Builder
        self.routing_engine = ValhallaRoutingAdapter(
            base_url=self.base_cfg["providers"]["routing"]["base_url"],
            road_graph=self.road_graph,
        )
        self.route_alert_engine = RouteAlertEngine(
            routing_engine=self.routing_engine,
            hotspot_isolator=self.hotspot_isolator,
            rule_translator=self.rule_translator,
            risk_threshold=cutoff,
        )

        logger.info("ServiceContainer initialized successfully", cache=cache_backend, nodes=self.road_graph.number_of_nodes())


_container_instance: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """Singleton getter for FastAPI dependency injection."""
    global _container_instance
    if _container_instance is None:
        _container_instance = ServiceContainer()
    return _container_instance
