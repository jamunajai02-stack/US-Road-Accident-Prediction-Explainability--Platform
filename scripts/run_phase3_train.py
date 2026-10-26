"""CLI script to run Phase 3: STGCN Model Training, Evaluation & ONNX Export."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import torch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libs.common.config import ConfigLoader
from libs.common.logger import logger
from modules.phase3_predictive_core.training.temporal_split import SpatioTemporalSplitter
from modules.phase3_predictive_core.training.trainer import STGCNPredictor, STGCNTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3: STGCN Model Training & Evaluation")
    parser.add_argument("--snapshots", type=str, default="data/processed/aligned_snapshots.pt")
    parser.add_argument("--onnx-output", type=str, default="data/processed/stgcn_model.onnx")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--temporal-backend", type=str, default="transformer", choices=["transformer", "convlstm"])
    parser.add_argument(
        "--max-snapshots",
        type=int,
        default=None,
        help="Optional cap on total snapshots used, applied as even time-stratified sampling",
    )
    args = parser.parse_args()

    model_cfg = ConfigLoader.load("model")
    logger.info("Initializing Phase 3 Training Pipeline", epochs=args.epochs, backend=args.temporal_backend)

    # 1. Load snapshots dataset
    if Path(args.snapshots).exists():
        snapshots = torch.load(args.snapshots, weights_only=False)
    else:
        logger.warn("Snapshots dataset not found, generating synthetic training snapshots")
        snapshots = []
        for i in range(12):
            dt = datetime(2021 if i < 6 else (2022 if i < 9 else 2023), (i % 12) + 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            snap = {
                "timestamp": dt,
                "x": torch.rand((16, 2), dtype=torch.float32),
                "edge_index": torch.tensor([[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 0]], dtype=torch.long),
                "edge_attr": torch.rand((6, 18), dtype=torch.float32),
                "y": (torch.rand((6, 1)) > 0.7).float(),
                "num_nodes": 16,
                "num_edges": 6,
            }
            snapshots.append(snap)

    # Sort snapshots chronologically
    snapshots.sort(key=lambda s: s["timestamp"])

    # 1b. Optional time-stratified sampling cap for tractable training.
    # Evenly spaced selection preserves the full temporal range (and therefore a
    # valid chronological train/val/test split) instead of truncating recent data.
    if args.max_snapshots and len(snapshots) > args.max_snapshots:
        step = len(snapshots) / float(args.max_snapshots)
        sampled = []
        last_idx = -1
        for i in range(args.max_snapshots):
            idx = min(int(round(i * step)), len(snapshots) - 1)
            if idx != last_idx:
                sampled.append(snapshots[idx])
                last_idx = idx
        logger.info(
            "Time-stratified snapshot sampling applied",
            original_count=len(snapshots),
            kept_count=len(sampled),
        )
        snapshots = sampled

    # 2. Chronological & Spatial Split (Patch 2)
    split_cfg = model_cfg.get("split", {})
    t_end = pd.to_datetime(split_cfg.get("train_end", "2021-12-31T23:59:59")).to_pydatetime()
    v_end = pd.to_datetime(split_cfg.get("val_end", "2022-12-31T23:59:59")).to_pydatetime()

    splitter = SpatioTemporalSplitter(
        train_end=t_end,
        val_end=v_end,
        spatial_holdout_ratio=float(split_cfg.get("spatial_holdout_ratio", 0.15)),
    )
    
    train_snaps, val_snaps, test_snaps = splitter.split_snapshots(snapshots)
    
    # If historical data spans within a single temporal slice, create chronological index partitions
    if len(val_snaps) == 0 or len(test_snaps) == 0:
        n = len(snapshots)
        n_train = max(1, int(n * 0.70))
        n_val = max(1, int(n * 0.15))
        train_snaps = snapshots[:n_train]
        val_snaps = snapshots[n_train : n_train + n_val]
        test_snaps = snapshots[n_train + n_val :] or val_snaps

    logger.info(
        "Training split partitions",
        train_snapshots=len(train_snaps),
        val_snapshots=len(val_snaps),
        test_snapshots=len(test_snaps),
    )

    # 3. Instantiate model
    model = STGCNPredictor(
        node_in_features=2,
        edge_in_features=18,
        hidden_channels=model_cfg["model"]["spatial_architecture"]["hidden_channels"],
        temporal_backend=args.temporal_backend,
        dropout=model_cfg["model"]["spatial_architecture"]["dropout"],
    )

    trainer = STGCNTrainer(
        model=model,
        learning_rate=float(model_cfg["training"]["learning_rate"]),
        weight_decay=float(model_cfg["training"]["weight_decay"]),
        pos_weight=float(model_cfg["training"]["pos_weight"]),
    )

    # 4. Training loop
    logger.info("Starting training loop", train_batches=len(train_snaps), val_batches=len(val_snaps))
    for epoch in range(1, args.epochs + 1):
        loss = trainer.train_epoch(train_snaps)
        val_metrics = trainer.evaluate(val_snaps)
        logger.info(
            f"Epoch {epoch}/{args.epochs}",
            train_loss=round(loss, 4),
            val_pr_auc=val_metrics["pr_auc"],
            val_brier=val_metrics["brier_score"],
        )

    # 5. Final test evaluation
    test_metrics = trainer.evaluate(test_snaps)
    logger.info("Test Evaluation Results", metrics=test_metrics)

    # 6. Export to ONNX / Weights for low-latency serving
    onnx_file = trainer.export_onnx(args.onnx_output, dummy_snapshot=train_snaps[0])
    logger.info("Phase 3 Complete: STGCN trained and exported to ONNX", onnx_path=onnx_file)


if __name__ == "__main__":
    main()
