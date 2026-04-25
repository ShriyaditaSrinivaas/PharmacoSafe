"""Tests for the ADR predictor model."""

import pytest
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, ".")

from pharmacosafe.data.generator import PharmacogenomicDataGenerator
from pharmacosafe.data.preprocessor import DataPreprocessor
from pharmacosafe.models.adr_predictor import ADRPredictor
from pharmacosafe.config import DataConfig, ModelConfig


class TestADRPredictor:

    def setup_method(self):
        config = DataConfig(n_samples=300, random_state=42)
        self.df = PharmacogenomicDataGenerator(config).generate()
        self.preprocessor = DataPreprocessor(ModelConfig(cv_folds=2, n_estimators=20))
        self.drug_id = "warfarin"

        X, y = self.preprocessor.prepare_features(self.df, self.drug_id)
        self.split = self.preprocessor.split(X, y, self.df["population"])

    def test_train_returns_metrics(self):
        model = ADRPredictor(ModelConfig(cv_folds=2, n_estimators=20))
        metrics = model.train(self.split["X_train"], self.split["y_train"], self.drug_id)
        assert "cv_auc_mean" in metrics
        assert 0 <= metrics["cv_auc_mean"] <= 1

    def test_predict_returns_probabilities(self):
        model = ADRPredictor(ModelConfig(cv_folds=2, n_estimators=20))
        model.train(self.split["X_train"], self.split["y_train"], self.drug_id)
        result = model.predict(self.split["X_test"])
        assert len(result["probabilities"]) == len(self.split["X_test"])
        assert all(0 <= p <= 1 for p in result["probabilities"])

    def test_predict_returns_risk_levels(self):
        model = ADRPredictor(ModelConfig(cv_folds=2, n_estimators=20))
        model.train(self.split["X_train"], self.split["y_train"], self.drug_id)
        result = model.predict(self.split["X_test"])
        valid_levels = {"Minimal", "Low", "Moderate", "High", "Critical"}
        assert all(r in valid_levels for r in result["risk_levels"])

    def test_evaluate_returns_auc(self):
        model = ADRPredictor(ModelConfig(cv_folds=2, n_estimators=20))
        model.train(self.split["X_train"], self.split["y_train"], self.drug_id)
        metrics = model.evaluate(self.split["X_test"], self.split["y_test"])
        assert "auc_roc" in metrics
        assert "brier_score" in metrics

    def test_model_is_fitted_flag(self):
        model = ADRPredictor()
        assert not model.is_fitted
        model.train(self.split["X_train"], self.split["y_train"], self.drug_id)
        assert model.is_fitted
