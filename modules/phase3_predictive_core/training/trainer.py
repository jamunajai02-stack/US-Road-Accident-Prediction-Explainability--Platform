"""STGCN model architecture, training loop, evaluation metrics, and ONNX exporter."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
import torch
import torch.nn as nn
import torch.optim as optim
from libs.common.logger import logger
from modules.phase3_predictive_core.probability_head.calibration import ElkanPriorCalibrator
from modules.phase3_predictive_core.probability_head.head import CalibratedProbabilityHead
from modules.phase3_predictive_core.stgcn.spatial_layer import SpatialGraphConv
from modules.phase3_predictive_core.temporal_sequencer.sequencer import build_temporal_encoder


class STGCNPredictor(nn.Module):
    """End-to-end Spatio-Temporal Graph Convolutional Network for segment-level accident forecasting."""

    def __init__(
        self,
        node_in_features: int = 2,
        edge_in_features: int = 18,
        hidden_channels: int = 32,
        temporal_backend: str = "transformer",
        dropout: float = 0.2,
    ):
        super().__init__()
        self.spatial_conv = SpatialGraphConv(
            in_features=node_in_features,
            out_features=hidden_channels,
            dropout=dropout,
        )
        self.temporal_encoder = build_temporal_encoder(
            backend=temporal_backend,
            d_model=hidden_channels,
            dropout=dropout,
        )
        self.probability_head = CalibratedProbabilityHead(
            in_features=hidden_channels,
            hidden_dim=16,
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass predicting accident probability for all edges.
        
        Args:
            x: (N, 2) node coordinates
            edge_index: (2, E) adjacency
            edge_attr: (E, 18) static + dynamic edge features
            
        Returns:
            (E, 1) probability tensor in [0.0, 1.0]
        """
        # 1. Spatial graph propagation
        _, edge_embed = self.spatial_conv(x, edge_index, edge_attr)
        
        # 2. Sequence projection (unsqueeze sequence dim [E, 1, hidden] for single frame or rolling)
        edge_seq = edge_embed.unsqueeze(1)
        temporal_context = self.temporal_encoder(edge_seq)
        
        # 3. Continuous probability head
        prob_out = self.probability_head(temporal_context)
        return prob_out


class STGCNTrainer:
    """Trains STGCN model on aligned graph snapshots with PR-AUC metric tracking and ONNX export."""

    def __init__(
        self,
        model: STGCNPredictor,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        pos_weight: float = 3.5,
    ):
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
        self.criterion = nn.BCELoss(weight=torch.tensor([pos_weight]))
        self.calibrator = ElkanPriorCalibrator(training_prior=1.0 / (1.0 + pos_weight))

    def train_epoch(self, train_snapshots: List[Dict[str, Any]]) -> float:
        """Execute one training epoch across graph snapshots."""
        self.model.train()
        total_loss = 0.0
        
        for snap in train_snapshots:
            self.optimizer.zero_grad()
            preds = self.model(snap["x"], snap["edge_index"], snap["edge_attr"])
            loss = self.criterion(preds, snap["y"])
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()

        return total_loss / max(1, len(train_snapshots))

    def evaluate(self, eval_snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate model and compute PR-AUC, ROC-AUC, and Brier calibration loss."""
        if not eval_snapshots:
            return {"pr_auc": 0.50, "roc_auc": 0.50, "brier_score": 0.05, "mean_calibrated_prob": 0.01}

        self.model.eval()
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for snap in eval_snapshots:
                preds = self.model(snap["x"], snap["edge_index"], snap["edge_attr"])
                all_preds.extend(preds.cpu().numpy().ravel())
                all_labels.extend(snap["y"].cpu().numpy().ravel())

        y_true = np.array(all_labels)
        y_prob_raw = np.array(all_preds)
        y_prob_calib = self.calibrator.calibrate(y_prob_raw)

        # Handle edge cases with zero positive samples in test slice
        if len(y_true) > 0 and np.sum(y_true) > 0 and np.sum(y_true) < len(y_true):
            pr_auc = float(average_precision_score(y_true, y_prob_calib))
            roc_auc = float(roc_auc_score(y_true, y_prob_calib))
        else:
            pr_auc = 0.50
            roc_auc = 0.50

        brier = float(brier_score_loss(y_true, y_prob_calib)) if len(y_true) > 0 else 0.05

        return {
            "pr_auc": round(pr_auc, 4),
            "roc_auc": round(roc_auc, 4),
            "brier_score": round(brier, 4),
            "mean_calibrated_prob": round(float(np.mean(y_prob_calib)), 4),
        }

    def export_onnx(self, output_path: str, dummy_snapshot: Dict[str, Any]) -> str:
        """Export trained PyTorch model to ONNX or serialized PyTorch weights.

        Always writes a `.pth` PyTorch weights artifact. The `.onnx` file is only
        produced on a genuinely successful `torch.onnx.export`; otherwise this
        method returns the `.pth` path and does NOT overwrite `.onnx` with a
        state dict (which previously made onnx files unreadable by onnxruntime).
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        self.model.eval()

        dummy_x = dummy_snapshot["x"]
        dummy_edge_index = dummy_snapshot["edge_index"]
        dummy_edge_attr = dummy_snapshot["edge_attr"]

        # 1. Always persist portable PyTorch weights.
        weights_path = out_file.with_suffix(".pth")
        torch.save(self.model.state_dict(), str(weights_path))

        # 2. Best-effort real ONNX export.
        try:
            export_kwargs = {
                "input_names": ["node_coords", "edge_index", "edge_features"],
                "output_names": ["risk_probabilities"],
                "opset_version": 14,
            }
            torch.onnx.export(
                self.model,
                (dummy_x, dummy_edge_index, dummy_edge_attr),
                str(out_file),
                **export_kwargs,
            )
            logger.info("Exported STGCN model to ONNX", path=str(out_file), weights_path=str(weights_path))
            return str(out_file)
        except Exception as e:
            logger.warn(
                "ONNX export failed; saved PyTorch weights artifact only",
                error=str(e),
                weights_path=str(weights_path),
            )
            return str(weights_path)
