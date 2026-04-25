"""
Training pipeline for PharmacoSafe.
Orchestrates data generation, preprocessing, model training, and evaluation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional

from pharmacosafe.config import DRUG_DATABASE, ModelConfig, DATA_DIR, MODELS_DIR
from pharmacosafe.data.generator import PharmacogenomicDataGenerator
from pharmacosafe.data.preprocessor import DataPreprocessor
from pharmacosafe.models.adr_predictor import ADRPredictor
from pharmacosafe.models.ensemble import StackingEnsemble


class TrainingPipeline:
    """Orchestrates the full training pipeline for all drug models."""

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.preprocessor = DataPreprocessor(self.config)
        self.models: Dict[str, ADRPredictor] = {}
        self.ensemble = StackingEnsemble(self.config)
        self.results: Dict[str, dict] = {}

    def run(self, df: pd.DataFrame, drugs: Optional[List[str]] = None) -> dict:
        """Run the full training pipeline."""
        if drugs is None:
            drugs = list(DRUG_DATABASE.keys())

        # Filter to drugs that have ADR columns
        valid_drugs = [d for d in drugs if f"adr_{d}" in df.columns]
        if not valid_drugs:
            raise ValueError("No valid drug ADR columns found in data.")

        # Create a single consistent train/test split for all drugs
        first_drug = valid_drugs[0]
        X_first, y_first = self.preprocessor.prepare_features(df, first_drug)
        split_first = self.preprocessor.split(X_first, y_first, df["population"])
        train_idx = split_first["X_train"].index
        test_idx = split_first["X_test"].index

        all_train_metrics = {}
        all_test_metrics = {}
        base_predictions_train = {}
        base_predictions_test = {}
        y_train_any = np.zeros(len(train_idx), dtype=int)
        y_test_any = np.zeros(len(test_idx), dtype=int)

        for drug_id in valid_drugs:
            target_col = f"adr_{drug_id}"

            # Prepare features using the same preprocessor
            X, y = self.preprocessor.prepare_features(df, drug_id)

            # Use the consistent split indices
            X_train = X.loc[train_idx]
            X_test = X.loc[test_idx]
            y_train = y.loc[train_idx]
            y_test = y.loc[test_idx]

            # Train
            model = ADRPredictor(self.config)
            train_metrics = model.train(X_train, y_train, drug_id)
            test_metrics = model.evaluate(X_test, y_test)

            all_train_metrics[drug_id] = train_metrics
            all_test_metrics[drug_id] = test_metrics
            self.models[drug_id] = model

            # Collect predictions for ensemble
            train_pred = model.predict(X_train)["probabilities"]
            test_pred = model.predict(X_test)["probabilities"]
            base_predictions_train[drug_id] = np.array(train_pred)
            base_predictions_test[drug_id] = np.array(test_pred)

            # Track any-ADR outcome
            y_train_any = np.maximum(y_train_any, y_train.values.astype(int))
            y_test_any = np.maximum(y_test_any, y_test.values.astype(int))

            # Save individual model
            model.save()

        # Train ensemble
        ensemble_metrics = {}
        if len(base_predictions_train) >= 2 and y_train_any is not None:
            ensemble_metrics = self.ensemble.train(base_predictions_train, y_train_any)
            self.ensemble.save()

        self.results = {
            "train_metrics": all_train_metrics,
            "test_metrics": all_test_metrics,
            "ensemble_metrics": ensemble_metrics,
            "n_drugs_trained": len(self.models),
        }
        return self.results

    def save_results(self):
        """Save training results to JSON."""
        import json
        results_path = MODELS_DIR / "training_results.json"
        with open(results_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        return results_path
