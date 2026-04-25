"""
SHAP Explainer for PharmacoSafe.
Provides per-patient and global explanations for ADR predictions.
"""

import numpy as np
import pandas as pd
import shap
from typing import Dict, Optional

from pharmacosafe.models.adr_predictor import ADRPredictor


class SHAPExplainer:
    """SHAP-based explainability for ADR predictions."""

    def __init__(self, model: ADRPredictor):
        if not model.is_fitted:
            raise RuntimeError("Model must be fitted before explaining.")
        self.model = model
        self.explainer = shap.TreeExplainer(model.model)

    def explain_patient(self, X: pd.DataFrame) -> dict:
        """Generate SHAP explanation for a single patient."""
        X_aligned = X.reindex(columns=self.model.feature_names, fill_value=0)
        shap_values = self.explainer.shap_values(X_aligned)

        # Handle different SHAP output formats
        if isinstance(shap_values, list):
            sv = shap_values[1][0]  # Binary: list of [class0, class1]
        elif shap_values.ndim == 2:
            sv = shap_values[0]     # Single array for GBM: shape (n_samples, n_features)
        else:
            sv = shap_values

        # Build feature contributions
        contributions = []
        for fname, sval in zip(self.model.feature_names, sv):
            fval = X_aligned[fname].iloc[0] if fname in X_aligned.columns else 0
            contributions.append({
                "feature": fname,
                "value": float(fval),
                "shap_value": float(sval),
                "impact": "increases_risk" if sval > 0 else "decreases_risk",
                "magnitude": abs(float(sval)),
            })

        # Sort by magnitude
        contributions.sort(key=lambda x: x["magnitude"], reverse=True)

        ev = self.explainer.expected_value
        if isinstance(ev, (list, np.ndarray)):
            base_value = float(ev[1]) if len(ev) > 1 else float(ev[0])
        else:
            base_value = float(ev)

        return {
            "drug_id": self.model.drug_id,
            "base_value": base_value,
            "contributions": contributions,
            "top_risk_factors": [c for c in contributions[:5] if c["shap_value"] > 0],
            "top_protective_factors": [c for c in contributions[:5] if c["shap_value"] < 0],
        }

    def global_importance(self, X: pd.DataFrame) -> dict:
        """Calculate global feature importance across all patients."""
        X_aligned = X.reindex(columns=self.model.feature_names, fill_value=0)
        shap_values = self.explainer.shap_values(X_aligned)

        if isinstance(shap_values, list):
            sv = shap_values[1]
        elif shap_values.ndim == 2:
            sv = shap_values
        else:
            sv = shap_values

        mean_abs = np.abs(sv).mean(axis=0)
        importance = dict(zip(self.model.feature_names, mean_abs.tolist()))
        sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        return {
            "drug_id": self.model.drug_id,
            "feature_importance": sorted_importance,
            "top_10": dict(list(sorted_importance.items())[:10]),
        }

    def population_stratified(self, X: pd.DataFrame, populations: pd.Series) -> dict:
        """SHAP analysis stratified by population."""
        X_aligned = X.reindex(columns=self.model.feature_names, fill_value=0)
        shap_values = self.explainer.shap_values(X_aligned)

        if isinstance(shap_values, list):
            sv = shap_values[1]
        elif shap_values.ndim == 2:
            sv = shap_values
        else:
            sv = shap_values

        results = {}
        for pop in populations.unique():
            mask = populations.values == pop
            if mask.sum() == 0:
                continue
            pop_sv = sv[mask]
            mean_abs = np.abs(pop_sv).mean(axis=0)
            importance = dict(zip(self.model.feature_names, mean_abs.tolist()))
            sorted_imp = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
            results[pop] = {"feature_importance": sorted_imp, "n_samples": int(mask.sum())}

        return {"drug_id": self.model.drug_id, "population_analysis": results}
