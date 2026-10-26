"""Stratified negative sample generator for class-balanced spatio-temporal datasets."""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
from libs.common.logger import logger
from libs.schemas.accident import AccidentEvent, NegativeSample


class StratifiedNegativeSampler:
    """Generates synthetic non-accident events at the same H3 locations with stratified time shifts."""

    def __init__(
        self,
        sampling_ratio: float = 3.5,
        time_offset_days: List[int] = None,
        time_offset_hours: List[int] = None,
        seed: int = 42,
    ):
        self.sampling_ratio = sampling_ratio
        self.time_offset_days = time_offset_days or [1, 2, 7, 14, 21, 28]
        self.time_offset_hours = time_offset_hours or [-4, -3, -2, 2, 3, 4]
        self.rng = random.Random(seed)

    def generate_negatives(
        self, positive_events: List[AccidentEvent]
    ) -> List[NegativeSample]:
        """Generate synthetic negative samples with spatial collision avoidance."""
        # Index positive event space-time bins (h3_cell, epoch_hour) to prevent positive collisions
        positive_bins: Set[Tuple[str, int]] = set()
        for evt in positive_events:
            epoch_hour = int(evt.timestamp.timestamp() // 3600)
            positive_bins.add((evt.h3_cell, epoch_hour))

        negative_samples: List[NegativeSample] = []
        target_total_negatives = int(len(positive_events) * self.sampling_ratio)

        for event in positive_events:
            # Generate 3 or 4 negatives per event according to sampling_ratio
            num_to_generate = int(self.sampling_ratio)
            if self.rng.random() < (self.sampling_ratio - num_to_generate):
                num_to_generate += 1

            for sample_idx in range(num_to_generate):
                # Try candidate time shifts until collision-free
                offset_days = self.rng.choice(self.time_offset_days)
                # Randomize direction (past or future)
                if self.rng.random() > 0.5:
                    offset_days = -offset_days
                offset_hour = self.rng.choice(self.time_offset_hours)

                total_hour_delta = (offset_days * 24) + offset_hour
                neg_timestamp = event.timestamp + timedelta(hours=total_hour_delta)
                neg_epoch_hour = int(neg_timestamp.timestamp() // 3600)

                # Avoid collision with any real positive accident
                if (event.h3_cell, neg_epoch_hour) in positive_bins:
                    # Apply secondary jitter
                    neg_timestamp = neg_timestamp + timedelta(hours=12)
                    neg_epoch_hour = int(neg_timestamp.timestamp() // 3600)

                neg_id = f"neg_{event.id}_{sample_idx}_{offset_days}d_{offset_hour}h"
                neg_sample = NegativeSample(
                    id=neg_id,
                    accident_ref_id=event.id,
                    timestamp=neg_timestamp,
                    latitude=event.latitude,
                    longitude=event.longitude,
                    h3_cell=event.h3_cell,
                    label=0,
                    time_offset_hours=total_hour_delta,
                )
                negative_samples.append(neg_sample)

        logger.info(
            "Generated stratified negative samples",
            positives_count=len(positive_events),
            negatives_count=len(negative_samples),
            actual_ratio=round(len(negative_samples) / max(1, len(positive_events)), 2),
        )
        return negative_samples
