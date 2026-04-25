"""
ADR Predictor for PharmacoSafe.
Gradient Boosting model for predicting adverse drug reaction risk,
with calibrated probabilities and per-drug models.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score
from sklearn.metrics import (
    roc_auc_score, brier_score_loss, precision_score,
    recall_score, f1_score, classification_report,
)
from typing import Dict, Optional, Tuple

from pharmacosafe.config import ModelConfig, MODELS_DIR


class ADRPredictor:
    """
    Gradient Boosting ADR risk predictor with calibrated probabilities.
    Trains per-drug models and provides risk scoring with confidence intervals.
    """

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.model = None
        self.calibrated_model = None
        self.drug_id = None
        self.feature_names = None
        self.cv_scores = None
        self.is_fitted = False

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        drug_id: str,
    ) -> dict:
        """
        Train the ADR predictor for a specific drug.

        Returns:
            Training metrics including CV AUC scores
        """
        self.drug_id = drug_id
        self.feature_names = list(X_train.columns)

        # Base model
        self.model = GradientBoostingClassifier(
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            learning_rate=self.config.learning_rate,
            min_samples_leaf=self.config.min_child_weight,
            subsample=self.config.subsample,
            max_features=self.config.colsample_bytree,
            random_state=self.config.random_state,
        )

        # Cross-validation
        self.cv_scores = cross_val_score(
            self.model, X_train, y_train,
            cv=self.config.cv_folds,
            scoring="roc_auc",
        )

        # Fit base model
        self.model.fit(X_train, y_train)

        # Calibrate
        self.calibrated_model = CalibratedClassifierCV(
            self.model,
            method=self.config.calibration_method,
            cv=3,
        )
        self.calibrated_model.fit(X_train, y_train)

        self.is_fitted = True

        return {
            "drug_id": drug_id,
            "cv_auc_mean": float(np.mean(self.cv_scores)),
            "cv_auc_std": float(np.std(self.cv_scores)),
            "cv_auc_scores": self.cv_scores.tolist(),
            "n_train_samples": len(X_train),
            "n_features": len(self.feature_names),
        }

    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> dict:
        """Evaluate model on test data."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call train() first.")

        y_prob = self.calibrated_model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        metrics = {
            "drug_id": self.drug_id,
            "n_test_samples": len(X_test),
            "auc_roc": float(roc_auc_score(y_test, y_prob)),
            "brier_score": float(brier_score_loss(y_test, y_prob)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "prevalence": float(y_test.mean()),
        }

        return metrics

    def predict(self, X: pd.DataFrame) -> dict:
        """
        Predict ADR risk for patient(s).

        Returns:
            Dict with probabilities, risk levels, and feature importances
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call train() first.")

        # Ensure feature alignment
        X_aligned = X.reindex(columns=self.feature_names, fill_value=0)

        # Predict probabilities
        probabilities = self.calibrated_model.predict_proba(X_aligned)[:, 1]

        # Risk levels
        risk_levels = []
        for prob in probabilities:
            if prob >= 0.7:
                risk_levels.append("Critical")
            elif prob >= 0.5:
                risk_levels.append("High")
            elif prob >= 0.3:
                risk_levels.append("Moderate")
            elif prob >= 0.15:
                risk_levels.append("Low")
            else:
                risk_levels.append("Minimal")

        # Feature importance from base model
        importances = dict(zip(
            self.feature_names,
            self.model.feature_importances_.tolist(),
        ))

        return {
            "drug_id": self.drug_id,
            "probabilities": probabilities.tolist(),
            "risk_levels": risk_levels,
            "feature_importances": importances,
        }

    def predict_single(self, X: pd.DataFrame) -> dict:
        """Predict for a single patient (convenience method)."""
        result = self.predict(X)
        return {
            "drug_id": result["drug_id"],
            "probability": result["probabilities"][0],
            "risk_level": result["risk_levels"][0],
            "risk_percent": round(result["probabilities"][0] * 100, 1),
            "feature_importances": result["feature_importances"],
        }

    def save(self, directory: Optional[Path] = None):
        """Save model to disk."""
        directory = directory or MODELS_DIR
        directory.mkdir(parents=True, exist_ok=True)

        model_data = {
            "model": self.model,
            "calibrated_model": self.calibrated_model,
            "drug_id": self.drug_id,
            "feature_names": self.feature_names,
            "cv_scores": self.cv_scores,
            "config": self.config,
        }
        filepath = directory / f"adr_predictor_{self.drug_id}.joblib"
        joblib.dump(model_data, filepath)
        return filepath

    @classmethod
    def load(cls, drug_id: str, directory: Optional[Path] = None) -> "ADRPredictor":
        """Load a saved model from disk."""
        directory = directory or MODELS_DIR
        filepath = directory / f"adr_predictor_{drug_id}.joblib"

        model_data = joblib.load(filepath)
        instance = cls(config=model_data["config"])
        instance.model = model_data["model"]
        instance.calibrated_model = model_data["calibrated_model"]
        instance.drug_id = model_data["drug_id"]
        instance.feature_names = model_data["feature_names"]
        instance.cv_scores = model_data["cv_scores"]
        instance.is_fitted = True

        return instance
