"""Abstract base class interface for model performance and data drift monitoring (Patch 8)."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional


class ModelMonitor(ABC):
    """Interface for logging model predictions against verified outcomes and computing drift metrics."""

    @abstractmethod
    def log_prediction_vs_outcome(
        self,
        prediction_id: str,
        edge_id: str,
        predicted_probability: float,
        actual_outcome: Optional[int],
        features: Dict[str, Any],
        latency_ms: float,
        timestamp: datetime,
    ) -> None:
        """Log a serving prediction record alongside realized ground-truth outcome."""
        pass

    @abstractmethod
    def compute_drift_metrics(
        self, window_start: datetime, window_end: datetime
    ) -> Dict[str, float]:
        """Compute Population Stability Index (PSI), Brier score calibration drift, and PR-AUC drift.
        
        Returns:
            Dictionary containing metrics e.g. {'psi_score': 0.08, 'brier_drift': 0.01}
        """
        pass
