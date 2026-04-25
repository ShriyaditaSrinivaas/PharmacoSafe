# Pharmacogenomics Methodology

## Overview

PharmacoSafe implements a pharmacogenomics-driven adverse drug reaction (ADR) prediction system that integrates genetic variant data with clinical features to provide personalized drug safety assessments.

## Pharmacogenomic Foundation

### Key Pharmacogenes

PharmacoSafe monitors 8 critical pharmacogenes that together influence the metabolism and safety of over 200 drugs:

| Gene | Function | Key Drugs Affected |
|------|----------|-------------------|
| **CYP2D6** | Metabolizes ~25% of all drugs | Codeine, Tamoxifen, Tramadol |
| **CYP2C19** | Activates prodrugs, metabolizes PPIs | Clopidogrel, Omeprazole |
| **CYP2C9** | Metabolizes anticoagulants, NSAIDs | Warfarin, Phenytoin |
| **CYP3A4** | Metabolizes ~50% of all drugs | Simvastatin, Tacrolimus |
| **DPYD** | Metabolizes fluoropyrimidines | 5-Fluorouracil, Capecitabine |
| **TPMT** | Metabolizes thiopurines | Azathioprine, Mercaptopurine |
| **UGT1A1** | Glucuronidation enzyme | Irinotecan, Atazanavir |
| **VKORC1** | Warfarin target enzyme | Warfarin |

### Metabolizer Phenotypes

Patients are classified into metabolizer phenotypes based on their genetic variants:

- **Poor Metabolizer (PM)**: Absent or minimal enzyme activity
- **Intermediate Metabolizer (IM)**: Reduced activity (~50%)
- **Normal Metabolizer (NM)**: Reference activity level
- **Rapid Metabolizer (RM)**: Increased activity (~150%)
- **Ultra-rapid Metabolizer (UM)**: Markedly increased activity (>200%)

### Population-Specific Allele Frequencies

Metabolizer phenotype distributions vary significantly across populations. For example, CYP2C19 Poor Metabolizer frequency:
- European: 3%
- African: 4%
- East Asian: 14%
- South Asian: 10%
- Admixed American: 5%

This variation is a key driver of population-level ADR disparities.

## ADR Prediction Model

### Architecture
- **Base Models**: Gradient Boosting classifiers (one per drug) with calibrated probabilities
- **Ensemble**: Stacking meta-learner combining base model predictions
- **Calibration**: Isotonic regression for probability calibration

### Features
- Pharmacogene metabolizer phenotypes (encoded)
- Clinical features: age, sex, weight, BMI, eGFR, ALT, co-medications
- Population ancestry
- Smoking status, diabetes flag

### Training
- Synthetic data with biologically plausible pharmacogenomic distributions
- 5-fold cross-validation for model selection
- Stratified train/test split preserving population distribution

## Clinical Decision Support

Recommendations follow CPIC (Clinical Pharmacogenetics Implementation Consortium) guidelines:
- Dosing adjustments based on metabolizer status
- Drug avoidance alerts for high-risk gene-drug pairs
- Alternative drug suggestions
- Monitoring recommendations

## Limitations

1. **Synthetic data**: Patterns may not fully capture real-world pharmacogenomic complexity
2. **Gene-gene interactions**: Current model treats genes independently
3. **Structural variants**: CYP2D6 copy number variations not fully modeled
4. **Environmental factors**: Diet, drug interactions, and other modulators not comprehensively included
