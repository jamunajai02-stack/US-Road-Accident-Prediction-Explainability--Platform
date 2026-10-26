# Phase 3: Deep Learning Predictive Core

## Purpose
Implements a hybrid Spatio-Temporal Graph Neural Network (STGCN + Transformer/ConvLSTM) that predicts continuous short-horizon (next 1-hour) accident probabilities per road segment, with leak-free chronological splitting and analytical sampling bias prior calibration.

## Architecture & Principles
- **Spatial Layer (`stgcn/`)**: `SpatialGraphConv` aggregates topological neighbor messages across intersections and embeds 18-channel static+dynamic edge attributes (including curvature and weather).
- **Temporal Sequencer (`temporal_sequencer/`)**: Swappable temporal context encoders (`TransformerTemporalEncoder` with multi-head self-attention vs. `ConvLSTMTemporalEncoder`), driven by `configs/model.yaml`.
- **Calibrated Probability Head (`probability_head/`)**:
  - Continuous regression head outputting probabilities in `[0.0, 1.0]`.
  - `ElkanPriorCalibrator` (Patch 4): adjusts output from synthetic sampling ratio ($\beta = 0.222$) to true sparse base rate ($\gamma = 0.005$) via Elkan's odds formula.
- **Chronological & Spatial Holdout Split (`training/temporal_split.py`)**: Strict historical time cutoffs (`train <= 2021`, `val 2022`, `test 2023`) and geographic H3 holdout partitions to detect overfitting.
- **Serving Export (`training/trainer.py`)**: Exports trained PyTorch weights to standard ONNX format for sub-10ms serving in Phase 5.

## Inputs & Outputs
- **Input**: Aligned PyG snapshot tensors from Phase 2 (`data/processed/aligned_snapshots.pt`).
- **Output**: Calibrated probability predictions and exported ONNX model (`data/processed/stgcn_model.onnx`).

## Standalone Training
```bash
python scripts/run_phase3_train.py --snapshots data/processed/aligned_snapshots.pt --epochs 10
```
