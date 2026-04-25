"""
Fairness Auditor for PharmacoSafe.
Evaluates model fairness across populations with demographic parity,
equalized odds, and calibration metrics.
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score, brier_score_loss
from typing import Dict, List, Optional

from pharmacosafe.config import FairnessConfig, POPULATION_NAMES


class FairnessAuditor:
    """Comprehensive fairness auditing engine for ADR prediction models."""

    def __init__(self, config: Optional[FairnessConfig] = None):
        self.config = config or FairnessConfig()

    def audit(self, y_true: np.ndarray, y_prob: np.ndarray,
              populations: np.ndarray, drug_id: str = "") -> dict:
        """Run full fairness audit."""
        results = {
            "drug_id": drug_id,
            "n_samples": len(y_true),
            "population_metrics": {},
            "demographic_parity": {},
            "equalized_odds": {},
            "calibration": {},
            "statistical_tests": {},
            "overall_fairness": {},
        }

        y_pred = (y_prob >= 0.5).astype(int)
        unique_pops = np.unique(populations)

        # Per-population metrics
        for pop in unique_pops:
            mask = populations == pop
            n_pop = mask.sum()
            if n_pop < 10:
                continue

            yt = y_true[mask]
            yp = y_prob[mask]
            ypred = y_pred[mask]

            metrics = {"population": pop, "name": POPULATION_NAMES.get(pop, pop), "n": int(n_pop)}

            try:
                metrics["auc"] = float(roc_auc_score(yt, yp))
            except ValueError:
                metrics["auc"] = None

            metrics["brier"] = float(brier_score_loss(yt, yp))
            metrics["positive_rate"] = float(ypred.mean())
            metrics["prevalence"] = float(yt.mean())

            tp = ((ypred == 1) & (yt == 1)).sum()
            fp = ((ypred == 1) & (yt == 0)).sum()
            fn = ((ypred == 0) & (yt == 1)).sum()
            tn = ((ypred == 0) & (yt == 0)).sum()

            metrics["sensitivity"] = float(tp / (tp + fn)) if (tp + fn) > 0 else None
            metrics["specificity"] = float(tn / (tn + fp)) if (tn + fp) > 0 else None
            metrics["ppv"] = float(tp / (tp + fp)) if (tp + fp) > 0 else None
            metrics["fpr"] = float(fp / (fp + tn)) if (fp + tn) > 0 else None

            results["population_metrics"][pop] = metrics

        # Demographic parity
        pos_rates = {p: m["positive_rate"] for p, m in results["population_metrics"].items()}
        if pos_rates:
            max_rate = max(pos_rates.values())
            min_rate = min(pos_rates.values())
            results["demographic_parity"] = {
                "disparity": round(max_rate - min_rate, 4),
                "max_group": max(pos_rates, key=pos_rates.get),
                "min_group": min(pos_rates, key=pos_rates.get),
                "passed": (max_rate - min_rate) <= self.config.demographic_parity_threshold,
            }

        # Equalized odds
        sensitivities = {p: m["sensitivity"] for p, m in results["population_metrics"].items() if m["sensitivity"] is not None}
        fprs = {p: m["fpr"] for p, m in results["population_metrics"].items() if m["fpr"] is not None}

        if sensitivities:
            tpr_disp = max(sensitivities.values()) - min(sensitivities.values())
            results["equalized_odds"]["tpr_disparity"] = round(tpr_disp, 4)
            results["equalized_odds"]["tpr_passed"] = tpr_disp <= self.config.equalized_odds_threshold

        if fprs:
            fpr_disp = max(fprs.values()) - min(fprs.values())
            results["equalized_odds"]["fpr_disparity"] = round(fpr_disp, 4)
            results["equalized_odds"]["fpr_passed"] = fpr_disp <= self.config.equalized_odds_threshold

        # Calibration
        briers = {p: m["brier"] for p, m in results["population_metrics"].items()}
        if briers:
            max_brier = max(briers.values())
            min_brier = min(briers.values())
            results["calibration"] = {
                "disparity": round(max_brier - min_brier, 4),
                "passed": (max_brier - min_brier) <= self.config.calibration_threshold,
            }

        # Statistical test (Kruskal-Wallis on predicted probabilities)
        groups = [y_prob[populations == p] for p in unique_pops if (populations == p).sum() >= 10]
        if len(groups) >= 2:
            stat, pval = stats.kruskal(*groups)
            results["statistical_tests"]["kruskal_wallis"] = {
                "statistic": round(float(stat), 4),
                "p_value": round(float(pval), 6),
                "significant": pval < 0.05,
            }

        # Overall
        checks = []
        if results["demographic_parity"].get("passed") is not None:
            checks.append(results["demographic_parity"]["passed"])
        if results["equalized_odds"].get("tpr_passed") is not None:
            checks.append(results["equalized_odds"]["tpr_passed"])
        if results["calibration"].get("passed") is not None:
            checks.append(results["calibration"]["passed"])

        results["overall_fairness"] = {
            "all_passed": all(checks) if checks else None,
            "n_checks": len(checks),
            "n_passed": sum(checks) if checks else 0,
        }

        return results
