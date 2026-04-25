"""
Bias Detector for PharmacoSafe.
Automated bias scanning with severity classification and intersectional analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional

from pharmacosafe.config import FairnessConfig, POPULATION_NAMES


class BiasDetector:
    """Automated bias detection with severity classification."""

    def __init__(self, config: Optional[FairnessConfig] = None):
        self.config = config or FairnessConfig()

    def scan(self, y_true: np.ndarray, y_prob: np.ndarray,
             demographics: pd.DataFrame, drug_id: str = "") -> dict:
        """Run comprehensive bias scan."""
        results = {"drug_id": drug_id, "single_attribute": [], "intersectional": [], "summary": {}}

        y_pred = (y_prob >= 0.5).astype(int)

        # Single-attribute analysis
        for attr in self.config.protected_attributes:
            if attr not in demographics.columns:
                continue
            attr_biases = self._analyze_attribute(y_true, y_pred, y_prob, demographics[attr].values, attr)
            results["single_attribute"].extend(attr_biases)

        # Intersectional analysis (pairs of attributes)
        attrs = [a for a in self.config.protected_attributes if a in demographics.columns]
        for i in range(len(attrs)):
            for j in range(i + 1, len(attrs)):
                inter_biases = self._analyze_intersection(
                    y_true, y_pred, y_prob, demographics, attrs[i], attrs[j]
                )
                results["intersectional"].extend(inter_biases)

        # Summary
        all_biases = results["single_attribute"] + results["intersectional"]
        severities = [b["severity"] for b in all_biases]
        results["summary"] = {
            "n_biases_detected": len(all_biases),
            "high": severities.count("high"),
            "moderate": severities.count("moderate"),
            "low": severities.count("low"),
            "negligible": severities.count("negligible"),
        }

        return results

    def _analyze_attribute(self, y_true, y_pred, y_prob, attr_values, attr_name):
        """Analyze bias for a single attribute."""
        biases = []
        groups = np.unique(attr_values)

        # Compute per-group error rates
        group_metrics = {}
        for g in groups:
            mask = attr_values == g
            if mask.sum() < 10:
                continue
            error_rate = float(np.mean(y_pred[mask] != y_true[mask]))
            pos_rate = float(np.mean(y_pred[mask]))
            group_metrics[g] = {"error_rate": error_rate, "positive_rate": pos_rate, "n": int(mask.sum())}

        if len(group_metrics) < 2:
            return biases

        # Check for disparities
        error_rates = {g: m["error_rate"] for g, m in group_metrics.items()}
        pos_rates = {g: m["positive_rate"] for g, m in group_metrics.items()}

        error_disp = max(error_rates.values()) - min(error_rates.values())
        pos_disp = max(pos_rates.values()) - min(pos_rates.values())

        if error_disp > 0.05:
            biases.append({
                "attribute": attr_name,
                "type": "error_rate_disparity",
                "disparity": round(error_disp, 4),
                "severity": self._classify_severity(error_disp),
                "worst_group": max(error_rates, key=error_rates.get),
                "best_group": min(error_rates, key=error_rates.get),
                "details": group_metrics,
            })

        if pos_disp > 0.05:
            biases.append({
                "attribute": attr_name,
                "type": "positive_rate_disparity",
                "disparity": round(pos_disp, 4),
                "severity": self._classify_severity(pos_disp),
                "worst_group": max(pos_rates, key=pos_rates.get),
                "best_group": min(pos_rates, key=pos_rates.get),
                "details": group_metrics,
            })

        return biases

    def _analyze_intersection(self, y_true, y_pred, y_prob, demographics, attr1, attr2):
        """Analyze bias at the intersection of two attributes."""
        biases = []
        combined = demographics[attr1].astype(str) + "_" + demographics[attr2].astype(str)
        groups = combined.unique()

        group_errors = {}
        for g in groups:
            mask = combined.values == g
            if mask.sum() < 10:
                continue
            group_errors[g] = float(np.mean(y_pred[mask] != y_true[mask]))

        if len(group_errors) < 2:
            return biases

        disp = max(group_errors.values()) - min(group_errors.values())
        if disp > 0.05:
            biases.append({
                "attribute": f"{attr1} × {attr2}",
                "type": "intersectional_error_disparity",
                "disparity": round(disp, 4),
                "severity": self._classify_severity(disp),
                "worst_group": max(group_errors, key=group_errors.get),
                "best_group": min(group_errors, key=group_errors.get),
            })

        return biases

    def _classify_severity(self, disparity: float) -> str:
        for level, threshold in sorted(self.config.severity_levels.items(), key=lambda x: x[1]):
            if disparity < threshold:
                return level
        return "high"
