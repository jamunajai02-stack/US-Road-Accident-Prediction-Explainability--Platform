"""Abstract base class interface for training experiment tracking (MLflow / W&B compatible)."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ExperimentTracker(ABC):
    """Interface for logging model parameters, training metrics, and exporting artifacts."""

    @abstractmethod
    def start_run(self, run_name: str, tags: Dict[str, str]) -> None:
        """Start a new experiment run."""
        pass

    @abstractmethod
    def log_params(self, params: Dict[str, Any]) -> None:
        """Log hyperparameters and configuration dictionaries."""
        pass

    @abstractmethod
    def log_metrics(self, metrics: Dict[str, float], step: int) -> None:
        """Log iteration or epoch metrics (loss, PR-AUC, ROC-AUC, Brier score)."""
        pass

    @abstractmethod
    def log_artifact(self, local_path: str, artifact_path: str) -> None:
        """Save a model checkpoint or ONNX artifact."""
        pass

    @abstractmethod
    def end_run(self, status: str = "FINISHED") -> None:
        """Complete the current run."""
        pass
