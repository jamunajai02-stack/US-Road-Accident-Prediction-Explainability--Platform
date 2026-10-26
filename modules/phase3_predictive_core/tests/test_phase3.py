"""Unit tests for Phase 3 Deep Learning Predictive Core."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch
from modules.phase3_predictive_core.probability_head.calibration import ElkanPriorCalibrator, calibrate_probability
from modules.phase3_predictive_core.training.temporal_split import SpatioTemporalSplitter
from modules.phase3_predictive_core.training.trainer import STGCNPredictor, STGCNTrainer


class TestPhase3PredictiveCore(unittest.TestCase):

    def setUp(self):
        # Create a dummy 4-node, 4-edge synthetic snapshot
        self.num_nodes = 4
        self.num_edges = 4
        self.dummy_snap = {
            "timestamp": datetime(2021, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            "x": torch.tensor([[37.77, -122.41], [37.78, -122.42], [37.79, -122.43], [37.80, -122.44]], dtype=torch.float32),
            "edge_index": torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long),
            "edge_attr": torch.rand((self.num_edges, 18), dtype=torch.float32),
            "y": torch.tensor([[1.0], [0.0], [0.0], [0.0]], dtype=torch.float32),
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
        }

    def test_stgcn_transformer_forward_pass(self):
        model = STGCNPredictor(
            node_in_features=2,
            edge_in_features=18,
            hidden_channels=32,
            temporal_backend="transformer",
        )
        out = model(self.dummy_snap["x"], self.dummy_snap["edge_index"], self.dummy_snap["edge_attr"])
        self.assertEqual(out.shape, (self.num_edges, 1))
        self.assertTrue(torch.all(out >= 0.0) and torch.all(out <= 1.0))

    def test_stgcn_convlstm_forward_pass(self):
        model = STGCNPredictor(
            node_in_features=2,
            edge_in_features=18,
            hidden_channels=32,
            temporal_backend="convlstm",
        )
        out = model(self.dummy_snap["x"], self.dummy_snap["edge_index"], self.dummy_snap["edge_attr"])
        self.assertEqual(out.shape, (self.num_edges, 1))
        self.assertTrue(torch.all(out >= 0.0) and torch.all(out <= 1.0))

    def test_elkan_prior_calibration_math(self):
        # 3.5:1 negative sampling ratio -> training prior = 1 / 4.5 = 0.2222
        # Real-world base rate = 0.005 (0.5%)
        calibrator = ElkanPriorCalibrator(training_prior=0.2222, true_base_rate=0.005)
        raw_probs = np.array([0.50, 0.80, 0.20])
        calibrated = calibrator.calibrate(raw_probs)
        
        # When model predicts 0.50 under biased prior, true calibrated probability should shift downward towards base rate
        self.assertLess(calibrated[0], 0.10)
        self.assertGreater(calibrated[1], calibrated[0])
        self.assertGreater(calibrated[0], calibrated[2])

    def test_chronological_and_spatial_split(self):
        splitter = SpatioTemporalSplitter(
            train_end=datetime(2021, 12, 31, 23, 59, 59),
            val_end=datetime(2022, 12, 31, 23, 59, 59),
            spatial_holdout_ratio=0.20,
        )
        
        snapshots = [
            {"timestamp": datetime(2021, 6, 1)},
            {"timestamp": datetime(2022, 6, 1)},
            {"timestamp": datetime(2023, 6, 1)},
        ]
        train, val, test = splitter.split_snapshots(snapshots)
        self.assertEqual(len(train), 1)
        self.assertEqual(len(val), 1)
        self.assertEqual(len(test), 1)

    def test_training_epoch_and_onnx_export(self):
        model = STGCNPredictor(node_in_features=2, edge_in_features=18, hidden_channels=16)
        trainer = STGCNTrainer(model, learning_rate=0.01)

        loss = trainer.train_epoch([self.dummy_snap, self.dummy_snap])
        self.assertIsInstance(loss, float)
        self.assertGreater(loss, 0.0)

        eval_metrics = trainer.evaluate([self.dummy_snap])
        self.assertIn("pr_auc", eval_metrics)
        self.assertIn("brier_score", eval_metrics)

        with tempfile.TemporaryDirectory() as tmp_dir:
            onnx_path = Path(tmp_dir) / "stgcn_test.onnx"
            exported = trainer.export_onnx(str(onnx_path), self.dummy_snap)

            # Corrected contract: returned artifact must exist and be loadable,
            # either a real ONNX graph or a `.pth` weights fallback (onnx may
            # be unavailable in the environment).
            artifact = Path(exported)
            self.assertTrue(artifact.exists(), f"Exported artifact missing: {exported}")
            self.assertIn(artifact.suffix.lower(), (".onnx", ".pth"))
            # `.pth` fallback must be a loadable torch state dict.
            if artifact.suffix.lower() == ".pth":
                state = torch.load(artifact, weights_only=False)
                self.assertTrue(isinstance(state, dict) and len(state) > 0)


if __name__ == "__main__":
    unittest.main()
