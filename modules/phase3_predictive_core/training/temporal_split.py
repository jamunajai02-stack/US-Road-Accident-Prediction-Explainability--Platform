"""Chronological and spatial holdout data splitting to prevent temporal and geographical data leakage (Patch 2)."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import pandas as pd
from libs.common.logger import logger


class SpatioTemporalSplitter:
    """Partitions time-series graph snapshots into chronological train/val/test sets with spatial holdouts."""

    def __init__(
        self,
        train_end: datetime = datetime(2021, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        val_end: datetime = datetime(2022, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        spatial_holdout_ratio: float = 0.15,
        salt: str = "accident_split_seed",
    ):
        self.train_end = self._ensure_utc(train_end)
        self.val_end = self._ensure_utc(val_end)
        self.spatial_holdout_ratio = spatial_holdout_ratio
        self.salt = salt

    @staticmethod
    def _ensure_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def is_spatial_holdout(self, h3_cell: str) -> bool:
        """Deterministic hash partition to mark geographic H3 cells as spatial test holdouts."""
        if not h3_cell:
            return False
        hash_digest = hashlib.md5(f"{h3_cell}_{self.salt}".encode("utf-8")).hexdigest()
        hash_val = int(hash_digest[:8], 16) / 0xFFFFFFFF
        return hash_val < self.spatial_holdout_ratio

    def split_snapshots(
        self, snapshots: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split list of 1-hour graph snapshots into Train, Validation, and Test partitions."""
        train_set = []
        val_set = []
        test_set = []

        for snap in snapshots:
            ts = snap["timestamp"]
            if isinstance(ts, str):
                ts = pd.to_datetime(ts).to_pydatetime()
            ts = self._ensure_utc(ts)

            if ts <= self.train_end:
                train_set.append(snap)
            elif ts <= self.val_end:
                val_set.append(snap)
            else:
                test_set.append(snap)

        logger.info(
            "Chronological snapshot partition complete",
            train_count=len(train_set),
            val_count=len(val_set),
            test_count=len(test_set),
        )
        return train_set, val_set, test_set
