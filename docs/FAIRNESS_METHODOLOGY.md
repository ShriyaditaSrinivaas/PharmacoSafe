# Fairness Methodology

## Overview

PharmacoSafe implements a comprehensive fairness assessment framework designed specifically for pharmacogenomic ADR prediction models. The framework evaluates model performance across protected population groups and provides actionable mitigation strategies.

## The Equity Problem in Pharmacogenomics

Most pharmacogenomic research has been conducted in European-ancestry populations. This creates two critical issues:

1. **Discovery bias**: Pharmacogenomic variants important in non-European populations may be undercharacterized
2. **Prediction bias**: ADR prediction models trained on biased data may underperform for underrepresented groups

PharmacoSafe explicitly addresses these gaps by:
- Generating synthetic data with realistic population-specific allele frequencies
- Auditing model performance across 5 ancestral populations
- Detecting and reporting intersectional biases

## Fairness Metrics

### 1. Demographic Parity
- **Definition**: Positive prediction rate should be similar across all groups
- **Threshold**: Maximum disparity ≤ 10%
- **Clinical relevance**: Ensures ADR screening rates are equitable

### 2. Equalized Odds
- **Definition**: True positive rates and false positive rates should be similar across groups
- **Threshold**: Maximum TPR/FPR disparity ≤ 10%
- **Clinical relevance**: Ensures equal detection accuracy across populations

### 3. Calibration
- **Definition**: Predicted probabilities should match observed rates per group
- **Threshold**: Maximum calibration gap ≤ 10%
- **Clinical relevance**: A 30% ADR risk prediction should mean ~30% actual risk, regardless of population

## Bias Detection

### Single-Attribute Analysis
Evaluates disparities for each protected attribute independently (population, sex, age group).

### Intersectional Analysis
Examines performance at intersections of multiple attributes (e.g., African-ancestry females, South Asian elderly).

### Severity Classification
- **Negligible**: Disparity < 5%
- **Low**: 5% ≤ Disparity < 10%
- **Moderate**: 10% ≤ Disparity < 20%
- **High**: Disparity ≥ 20%

## Statistical Testing
- Kruskal-Wallis test for inter-group prediction distribution differences
- Significance level: α = 0.05

## Disclaimer
This is a research demonstration using synthetic data. It is not intended for clinical use.
