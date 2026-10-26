"""Overpass API debug adapter for localized ad-hoc bounding-box queries (Patch 3)."""

from typing import Any, Dict, List, Optional
import httpx
from libs.common.exceptions import GraphStoreError
from libs.common.logger import logger
from libs.schemas.graph import SubgraphQuery
from modules.phase0_5_graph_extraction.graph_builder import RoadGraphBuilder


class OverpassDebugAdapter:
    """Debug-only adapter for querying small bounding boxes via Overpass API without production dependency."""

    def __init__(self, endpoint_url: str = "https://overpass-api.de/api/interpreter", timeout_seconds: int = 15):
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds

    async def fetch_debug_subgraph(self, query: SubgraphQuery) -> RoadGraphBuilder:
        """Fetch small localized intersection graph for visual debugging."""
        delta = query.radius_km / 111.0  # approximate degrees
        south = query.center_latitude - delta
        north = query.center_latitude + delta
        west = query.center_longitude - delta
        east = query.center_longitude + delta

        overpass_ql = f"""
        [out:json][timeout:{self.timeout_seconds}];
        (
          way["highway"]({south},{west},{north},{east});
          >;
        );
        out body;
        """

        logger.info("Executing Overpass debug query", bbox=[south, west, north, east])
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.endpoint_url, data={"data": overpass_ql})
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            raise GraphStoreError(f"Overpass debug query failed: {e}") from e

        builder = RoadGraphBuilder()
        nodes_dict: Dict[int, Dict[str, float]] = {}
        
        for element in data.get("elements", []):
            if element.get("type") == "node":
                node_id = element["id"]
                lat = element["lat"]
                lon = element["lon"]
                nodes_dict[node_id] = {"lat": lat, "lon": lon}
                builder.add_node(node_id, lat, lon)

        for element in data.get("elements", []):
            if element.get("type") == "way" and "nodes" in element:
                way_nodes = element["nodes"]
                tags = element.get("tags", {})
                highway = tags.get("highway", "secondary")
                maxspeed = float(tags.get("maxspeed", "50").replace(" mph", "").replace(" km/h", "") or 50.0)
                oneway = tags.get("oneway") == "yes"

                for i in range(len(way_nodes) - 1):
                    u = way_nodes[i]
                    v = way_nodes[i + 1]
                    if u in nodes_dict and v in nodes_dict:
                        coords = [
                            (nodes_dict[u]["lat"], nodes_dict[u]["lon"]),
                            (nodes_dict[v]["lat"], nodes_dict[v]["lon"]),
                        ]
                        builder.add_edge(
                            source_id=u,
                            target_id=v,
                            osm_way_id=element["id"],
                            coordinates=coords,
                            speed_limit_kmh=maxspeed,
                            highway_type=highway,
                            is_oneway=oneway,
                        )

        return builder
