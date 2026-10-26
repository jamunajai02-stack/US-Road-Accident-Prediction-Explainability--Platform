"""Abstract base class interface for model inference execution (ONNX / PyTorch)."""

from abc import ABC, abstractmethod
from typing import Dict, List
import numpy as np
from libs.schemas.prediction import EdgeRiskPrediction, ProbabilityOutput


class ModelRunner(ABC):
    """Interface for running fast spatio-temporal inference against road graph features."""

    @abstractmethod
    def predict_proba(self, node_features: np.ndarray, edge_index: np.ndarray, edge_features: np.ndarray) -> np.ndarray:
        """Run forward pass and return calibrated probability scores for each edge.
        
        Args:
            node_features: (N, T, F_node) or (N, F_node) tensor
            edge_index: (2, E) adjacency array
            edge_features: (E, T, F_edge) dynamic feature tensor
            
        Returns:
            (E,) array of continuous calibrated probabilities in [0.0, 1.0]
        """
        pass

    @abstractmethod
    def predict_subgraph_edges(
        self, edge_ids: List[str], features_map: Dict[str, Dict[str, float]]
    ) -> List[EdgeRiskPrediction]:
        """Convenience method to predict calibrated risk scores for a specified batch of edge IDs."""
        pass
