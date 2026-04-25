"""
Ensemble model for PharmacoSafe.
Stacking ensemble combining base ADR predictors with bootstrap CIs.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from typing import Dict, Optional

from pharmacosafe.config import MODELS_DIR, ModelConfig


class StackingEnsemble:
    """Stacking meta-learner combining base ADR predictors."""

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.meta_model = LogisticRegression(max_iter=1000, random_state=self.config.random_state)
        self.drug_ids = []
        self.is_fitted = False

    def train(self, base_predictions: Dict[str, np.ndarray], y_true: pd.Series) -> dict:
        X_meta = np.column_stack(list(base_predictions.values()))
        self.drug_ids = list(base_predictions.keys())
        self.meta_model.fit(X_meta, y_true)
        self.is_fitted = True
        y_prob = self.meta_model.predict_proba(X_meta)[:, 1]
        auc = roc_auc_score(y_true, y_prob)
        return {"ensemble_train_auc": float(auc), "n_base_models": len(self.drug_ids)}

    def predict(self, base_predictions: Dict[str, np.ndarray], n_bootstrap: int = 100) -> dict:
        if not self.is_fitted:
            raise RuntimeError("Ensemble not fitted.")
        X_meta = np.column_stack([base_predictions.get(d, np.zeros(len(next(iter(base_predictions.values()))))) for d in self.drug_ids])
        probabilities = self.meta_model.predict_proba(X_meta)[:, 1]
        rng = np.random.RandomState(self.config.random_state)
        boot_preds = []
        for _ in range(n_bootstrap):
            noise = rng.normal(0, 0.02, size=X_meta.shape)
            boot_preds.append(self.meta_model.predict_proba(X_meta + noise)[:, 1])
        boot_array = np.array(boot_preds)
        return {
            "probabilities": probabilities.tolist(),
            "ci_lower": np.percentile(boot_array, 2.5, axis=0).tolist(),
            "ci_upper": np.percentile(boot_array, 97.5, axis=0).tolist(),
        }

    def save(self, directory: Optional[Path] = None):
        directory = directory or MODELS_DIR
        directory.mkdir(parents=True, exist_ok=True)
        joblib.dump({"meta_model": self.meta_model, "drug_ids": self.drug_ids, "config": self.config}, directory / "ensemble_model.joblib")

    @classmethod
    def load(cls, directory: Optional[Path] = None) -> "StackingEnsemble":
        directory = directory or MODELS_DIR
        data = joblib.load(directory / "ensemble_model.joblib")
        instance = cls(config=data["config"])
        instance.meta_model = data["meta_model"]
        instance.drug_ids = data["drug_ids"]
        instance.is_fitted = True
        return instance
