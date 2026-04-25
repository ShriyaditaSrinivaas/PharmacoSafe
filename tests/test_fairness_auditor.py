"""Tests for the fairness auditor."""

import pytest
import numpy as np
import sys
sys.path.insert(0, ".")

from pharmacosafe.fairness.auditor import FairnessAuditor
from pharmacosafe.fairness.bias_detector import BiasDetector
from pharmacosafe.config import FairnessConfig
import pandas as pd


class TestFairnessAuditor:

    def setup_method(self):
        self.auditor = FairnessAuditor()
        np.random.seed(42)
        n = 500
        self.y_true = np.random.binomial(1, 0.3, n)
        self.y_prob = np.clip(self.y_true * 0.7 + np.random.normal(0, 0.2, n), 0, 1)
        self.populations = np.random.choice(["EUR", "AFR", "EAS"], size=n, p=[0.4, 0.35, 0.25])

    def test_audit_returns_population_metrics(self):
        result = self.auditor.audit(self.y_true, self.y_prob, self.populations)
        assert "population_metrics" in result
        assert len(result["population_metrics"]) >= 3

    def test_audit_returns_demographic_parity(self):
        result = self.auditor.audit(self.y_true, self.y_prob, self.populations)
        assert "disparity" in result["demographic_parity"]

    def test_audit_returns_overall_fairness(self):
        result = self.auditor.audit(self.y_true, self.y_prob, self.populations)
        assert "all_passed" in result["overall_fairness"]

    def test_audit_returns_statistical_tests(self):
        result = self.auditor.audit(self.y_true, self.y_prob, self.populations)
        assert "kruskal_wallis" in result["statistical_tests"]

    def test_per_population_auc(self):
        result = self.auditor.audit(self.y_true, self.y_prob, self.populations)
        for pop, metrics in result["population_metrics"].items():
            if metrics.get("auc") is not None:
                assert 0 <= metrics["auc"] <= 1


class TestBiasDetector:

    def setup_method(self):
        self.detector = BiasDetector()
        np.random.seed(42)
        n = 500
        self.y_true = np.random.binomial(1, 0.3, n)
        self.y_prob = np.clip(self.y_true * 0.7 + np.random.normal(0, 0.2, n), 0, 1)
        self.demographics = pd.DataFrame({
            "population": np.random.choice(["EUR", "AFR", "EAS"], n),
            "sex": np.random.choice(["Male", "Female"], n),
            "age_group": np.random.choice(["Young", "Middle", "Senior"], n),
        })

    def test_scan_returns_summary(self):
        result = self.detector.scan(self.y_true, self.y_prob, self.demographics)
        assert "summary" in result
        assert "n_biases_detected" in result["summary"]

    def test_scan_detects_single_attribute(self):
        result = self.detector.scan(self.y_true, self.y_prob, self.demographics)
        assert "single_attribute" in result

    def test_scan_detects_intersectional(self):
        result = self.detector.scan(self.y_true, self.y_prob, self.demographics)
        assert "intersectional" in result

    def test_severity_classification(self):
        result = self.detector.scan(self.y_true, self.y_prob, self.demographics)
        if result["single_attribute"]:
            for bias in result["single_attribute"]:
                assert bias["severity"] in ["negligible", "low", "moderate", "high"]
