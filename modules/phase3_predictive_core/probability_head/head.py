"""Continuous probability prediction head."""

import torch
import torch.nn as nn


class CalibratedProbabilityHead(nn.Module):
    """Multi-layer regression head predicting calibrated continuous probability P(accident) in [0.0, 1.0]."""

    def __init__(self, in_features: int = 32, hidden_dim: int = 16, temperature: float = 1.0):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
        )
        self.temperature = nn.Parameter(torch.tensor([temperature], dtype=torch.float32), requires_grad=False)

    def forward(self, edge_representations: torch.Tensor) -> torch.Tensor:
        """Args:
            edge_representations: (E, in_features)
        Returns:
            (E, 1) continuous probabilities in [0.0, 1.0]
        """
        logits = self.mlp(edge_representations) / torch.clamp(self.temperature, min=0.1)
        return torch.sigmoid(logits)
