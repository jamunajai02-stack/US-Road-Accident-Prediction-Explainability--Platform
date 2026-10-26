"""Probability calibration module correcting for synthetic negative sampling bias (Patch 4)."""

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from libs.schemas.prediction import ProbabilityOutput


class ElkanPriorCalibrator:
    """Corrects probability estimates from biased synthetic sampling ratio to real-world base rates.
    
    References:
        Elkan, Charles (2001). "The Foundations of Cost-Sensitive Learning". IJCAI.
    """

    def __init__(self, training_prior: float = 0.222, true_base_rate: float = 0.005):
        """Args:
            training_prior: Class 1 ratio in training dataset (e.g., 1 / (1 + 3.5) = 0.222)
            true_base_rate: True unconditioned base rate of accidents per segment-hour in real world
        """
        self.beta = max(1e-6, min(1.0 - 1e-6, training_prior))
        self.gamma = max(1e-6, min(1.0 - 1e-6, true_base_rate))
        self.odds_ratio = (self.gamma / (1.0 - self.gamma)) / (self.beta / (1.0 - self.beta))

    def calibrate(self, raw_probs: np.ndarray) -> np.ndarray:
        """Apply analytical prior-shift odds transformation to raw model probabilities."""
        p = np.clip(raw_probs, 1e-7, 1.0 - 1e-7)
        # Prior shift formula: p_true = (p * (gamma / (1-gamma))) / (p * (gamma / (1-gamma)) + (1-p) * (beta / (1-beta)))
        num = p * self.odds_ratio
        denom = num + (1.0 - p)
        calibrated = num / denom
        return np.clip(calibrated, 0.0, 1.0)


class EmpiricalCalibrator:
    """Supervised calibrator fitting Platt scaling or Isotonic regression on held-out validation set."""

    def __init__(self, method: str = "platt"):
        self.method = method
        if method == "platt":
            self.model = LogisticRegression(C=1.0, solver="lbfgs")
        elif method == "isotonic":
            self.model = IsotonicRegression(out_of_bounds="clip")
        else:
            raise ValueError(f"Unknown calibration method: {method}")

    def fit(self, val_probs: np.ndarray, y_true: np.ndarray) -> None:
        """Fit calibration curve on validation logits / probabilities."""
        val_probs_2d = val_probs.reshape(-1, 1) if self.method == "platt" else val_probs.ravel()
        self.model.fit(val_probs_2d, y_true.ravel())

    def calibrate(self, raw_probs: np.ndarray) -> np.ndarray:
        """Predict calibrated probabilities."""
        raw_probs = np.clip(raw_probs, 0.0, 1.0)
        if self.method == "platt":
            return self.model.predict_proba(raw_probs.reshape(-1, 1))[:, 1]
        elif self.method == "isotonic":
            return np.clip(self.model.predict(raw_probs.ravel()), 0.0, 1.0)


def calibrate_probability(
    raw_p: float,
    training_ratio: float = 3.5,
    true_base_rate: float = 0.005,
    method: str = "elkan_log_odds",
) -> ProbabilityOutput:
    """Helper function to transform raw sigmoid output into calibrated ProbabilityOutput schema."""
    training_prior = 1.0 / (1.0 + training_ratio)
    calibrator = ElkanPriorCalibrator(training_prior=training_prior, true_base_rate=true_base_rate)
    
    calibrated_val = float(calibrator.calibrate(np.array([raw_p]))[0])
    
    return ProbabilityOutput(
        raw_probability=round(raw_p, 4),
        calibrated_probability=round(calibrated_val, 4),
        probability_percentage=round(calibrated_val * 100.0, 2),
        calibration_method=method,
    )
