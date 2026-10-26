"""Spatial indexing module for assigning H3 hexagonal grid cells to accident records (Patch 1)."""

import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Iterator, List, Optional
import pandas as pd
from libs.common.exceptions import SpatialIndexingError
from libs.common.geo import GeoUtils
from libs.common.logger import logger
from libs.schemas.accident import AccidentEvent


class SpatialIndexer:
    """Ingests raw accident data and computes H3 spatial indices (res 7-9) without road snapping."""

    def __init__(self, h3_resolution: int = 8):
        self.h3_resolution = h3_resolution

    def parse_csv_stream(
        self,
        csv_path_or_zip: str,
        chunk_size: int = 10000,
        max_records: Optional[int] = None,
    ) -> Iterator[List[AccidentEvent]]:
        """Stream chunks of raw CSV/ZIP records and yield parsed AccidentEvent lists."""
        path = Path(csv_path_or_zip)
        if not path.exists():
            raise SpatialIndexingError(f"Dataset path does not exist: {path.resolve()}")

        logger.info("Opening dataset file for streaming", path=str(path), chunk_size=chunk_size)

        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path, "r") as z:
                csv_files = [f for f in z.namelist() if f.endswith(".csv")]
                if not csv_files:
                    raise SpatialIndexingError(f"No CSV file found inside archive: {path.name}")
                with z.open(csv_files[0]) as csv_file:
                    yield from self._process_chunks(csv_file, chunk_size, max_records)
        else:
            with open(path, "rb") as csv_file:
                yield from self._process_chunks(csv_file, chunk_size, max_records)

    def _process_chunks(
        self, file_obj: Any, chunk_size: int, max_records: Optional[int]
    ) -> Iterator[List[AccidentEvent]]:
        records_yielded = 0
        
        # Columns of interest in Kaggle US Accidents dataset
        usecols = ["ID", "Severity", "Start_Time", "Start_Lat", "Start_Lng", "Source"]
        
        try:
            reader = pd.read_csv(
                file_obj,
                usecols=lambda col: col in usecols,
                chunksize=chunk_size,
                low_memory=False,
            )
        except Exception:
            # Fallback if specific columns not present
            file_obj.seek(0)
            reader = pd.read_csv(file_obj, chunksize=chunk_size, low_memory=False)

        for chunk in reader:
            events: List[AccidentEvent] = []
            for _, row in chunk.iterrows():
                # Extract coordinates
                lat = row.get("Start_Lat") or row.get("latitude") or row.get("lat")
                lon = row.get("Start_Lng") or row.get("longitude") or row.get("lng")
                if pd.isna(lat) or pd.isna(lon):
                    continue

                lat = float(lat)
                lon = float(lon)
                if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                    continue

                # Parse timestamp
                raw_time = row.get("Start_Time") or row.get("timestamp") or datetime.utcnow()
                if isinstance(raw_time, str):
                    try:
                        ts = pd.to_datetime(raw_time).to_pydatetime()
                    except Exception:
                        ts = datetime.utcnow()
                elif isinstance(raw_time, datetime):
                    ts = raw_time
                else:
                    ts = datetime.utcnow()

                # Assign H3 cell index (Patch 1: H3 cell only, no edge_id)
                h3_cell = GeoUtils.lat_lng_to_h3(lat, lon, self.h3_resolution)
                rec_id = str(row.get("ID") or f"acc_{records_yielded + len(events)}")
                sev = int(row.get("Severity", 2)) if not pd.isna(row.get("Severity", 2)) else 2

                event = AccidentEvent(
                    id=rec_id,
                    timestamp=ts,
                    latitude=lat,
                    longitude=lon,
                    h3_cell=h3_cell,
                    severity=max(1, min(4, sev)),
                    source=str(row.get("Source", "kaggle")),
                )
                events.append(event)

                if max_records and (records_yielded + len(events)) >= max_records:
                    break

            records_yielded += len(events)
            if events:
                yield events

            if max_records and records_yielded >= max_records:
                break
