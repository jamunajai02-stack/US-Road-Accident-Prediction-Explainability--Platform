"""Swappable temporal sequencer backends: TransformerEncoder and ConvLSTM."""

from abc import ABC, abstractmethod
from typing import Tuple
import torch
import torch.nn as nn


class BaseTemporalEncoder(nn.Module, ABC):
    """Abstract interface for temporal sequencing over rolling time window (t-K to t)."""

    @abstractmethod
    def forward(self, x_seq: torch.Tensor) -> torch.Tensor:
        """Args:
            x_seq: (Batch, Sequence_Len, Features)
        Returns:
            (Batch, Hidden_Dim) context vector representing latest time step
        """
        pass


class TransformerTemporalEncoder(BaseTemporalEncoder):
    """Multi-head self-attention temporal encoder capturing long-range seasonal and weather trends."""

    def __init__(
        self,
        d_model: int = 32,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.1,
    ):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.out_proj = nn.Linear(d_model, d_model)

    def forward(self, x_seq: torch.Tensor) -> torch.Tensor:
        # x_seq: (Batch, Sequence_Len, d_model)
        out = self.transformer(x_seq)
        # Take representation at latest time step t
        latest_t = out[:, -1, :]
        return self.out_proj(latest_t)


class ConvLSTMTemporalEncoder(BaseTemporalEncoder):
    """Convolutional/Recurrent LSTM temporal encoder for sequential time-series modeling."""

    def __init__(self, in_channels: int = 32, hidden_dim: int = 32, num_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=in_channels,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, x_seq: torch.Tensor) -> torch.Tensor:
        # x_seq: (Batch, Sequence_Len, in_channels)
        out, (h_n, c_n) = self.lstm(x_seq)
        latest_t = h_n[-1]
        return self.out_proj(latest_t)


def build_temporal_encoder(
    backend: str = "transformer", d_model: int = 32, **kwargs
) -> BaseTemporalEncoder:
    """Factory function to build configured temporal encoder."""
    if backend.lower() == "transformer":
        return TransformerTemporalEncoder(
            d_model=d_model,
            nhead=kwargs.get("nhead", 4),
            num_layers=kwargs.get("num_layers", 2),
            dim_feedforward=kwargs.get("dim_feedforward", 128),
            dropout=kwargs.get("dropout", 0.1),
        )
    elif backend.lower() in ("convlstm", "lstm"):
        return ConvLSTMTemporalEncoder(
            in_channels=d_model,
            hidden_dim=d_model,
            num_layers=kwargs.get("num_layers", 2),
        )
    else:
        raise ValueError(f"Unknown temporal backend: {backend}")
