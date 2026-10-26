"""Standalone streaming worker process ingesting live weather radar and DOT incident feeds."""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from libs.common.config import ConfigLoader
from libs.common.logger import logger
from services.api_gateway.dependencies import get_service_container


async def main() -> None:
    logger.info("Initializing Background Streaming Ingestion Worker")
    container = get_service_container()

    # Continuously poll State 511 incidents and write to FeatureCache
    from modules.phase5_realtime_service.stream_ingestion.state511_adapter import State511Adapter
    state_adapter = State511Adapter(feature_cache=container.feature_cache, poll_interval_seconds=30)

    logger.info("Worker started listening to live feeds. Press Ctrl+C to stop.")
    try:
        async for incident in state_adapter.stream_incidents(region_code="CA"):
            logger.info("Processed live traffic incident event", incident_id=incident.get("properties", {}).get("id"))
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Worker shutting down gracefully")


if __name__ == "__main__":
    asyncio.run(main())
