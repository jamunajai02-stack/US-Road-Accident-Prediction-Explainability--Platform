"""Spatial graph convolution layer for spatio-temporal road risk propagation."""

from typing import Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class SpatialGraphConv(nn.Module):
    """Spatio-temporal graph convolution operating over directed road network topology."""

    def __init__(self, in_features: int = 2, out_features: int = 32, dropout: float = 0.2):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.linear_self = nn.Linear(in_features, out_features, bias=False)
        self.linear_nbr = nn.Linear(out_features, out_features, bias=True)
        self.linear_edge = nn.Linear(18, out_features, bias=False)
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(out_features)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass propagating spatial risk across connected road segments.
        
        Args:
            x: Node feature tensor (N, in_features)
            edge_index: Adjacency index (2, E)
            edge_attr: Edge feature tensor (E, 18)
            
        Returns:
            Tuple of (updated_node_features [N, out_features], updated_edge_features [E, out_features])
        """
        N = x.size(0)
        E = edge_index.size(1)

        src_nodes = edge_index[0]
        tgt_nodes = edge_index[1]

        # 1. Project node self features: (N, in_features) -> (N, out_features)
        h_self = self.linear_self(x)

        # 2. Compute edge representations by combining projected source/target nodes and edge attributes
        edge_embed = self.linear_edge(edge_attr) + h_self[src_nodes] + h_self[tgt_nodes]
        edge_embed = F.relu(edge_embed)
        edge_embed = self.dropout(edge_embed)

        # 3. Message passing: aggregate incoming edge and neighbor features at target nodes
        msg = edge_embed + h_self[src_nodes]
        aggr = torch.zeros((N, self.out_features), device=x.device, dtype=x.dtype)
        
        # Scatter-add incoming messages
        aggr.index_add_(0, tgt_nodes, self.linear_nbr(msg))

        # 4. Degree normalization
        degrees = torch.zeros((N, 1), device=x.device, dtype=x.dtype)
        degrees.index_add_(0, tgt_nodes, torch.ones((E, 1), device=x.device, dtype=x.dtype))
        degrees = torch.clamp(degrees, min=1.0)
        aggr_norm = aggr / degrees

        # 5. Combine self and neighbor representations with residual layer norm
        h_out = self.layer_norm(h_self + F.relu(aggr_norm))
        return h_out, edge_embed
