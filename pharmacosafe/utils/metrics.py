"""
Evaluation metrics for PharmacoSafe.
"""

import numpy as np
from sklearn.metrics import roc_auc_score, brier_score_loss, precision_recall_curve, auc


def calculate_metrics(y_true, y_prob, threshold=0.5):
    """Calculate comprehensive evaluation metrics."""
    y_pred = (np.array(y_prob) >= threshold).astype(int)
    y_true = np.array(y_true)

    tp = ((y_pred == 1) & (y_true == 1)).sum()
    fp = ((y_pred == 1) & (y_true == 0)).sum()
    fn = ((y_pred == 0) & (y_true == 1)).sum()
    tn = ((y_pred == 0) & (y_true == 0)).sum()

    metrics = {
        "n": len(y_true),
        "prevalence": float(y_true.mean()),
        "sensitivity": float(tp / (tp + fn)) if (tp + fn) > 0 else 0,
        "specificity": float(tn / (tn + fp)) if (tn + fp) > 0 else 0,
        "ppv": float(tp / (tp + fp)) if (tp + fp) > 0 else 0,
        "npv": float(tn / (tn + fn)) if (tn + fn) > 0 else 0,
        "accuracy": float((tp + tn) / len(y_true)) if len(y_true) > 0 else 0,
    }

    try:
        metrics["auc_roc"] = float(roc_auc_score(y_true, y_prob))
    except ValueError:
        metrics["auc_roc"] = None

    metrics["brier_score"] = float(brier_score_loss(y_true, y_prob))

    try:
        precision, recall, _ = precision_recall_curve(y_true, y_prob)
        metrics["auc_pr"] = float(auc(recall, precision))
    except ValueError:
        metrics["auc_pr"] = None

    return metrics
