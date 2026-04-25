<div align="center">

# 💊 PharmacoSafe

### Pharmacogenomics-Driven Adverse Drug Reaction Predictor with Fairness Auditing

[![CI](https://github.com/ShriyaditaSrinivaas/PharmacoSafe/actions/workflows/ci.yml/badge.svg)](https://github.com/ShriyaditaSrinivaas/PharmacoSafe/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

*Precision drug safety that works for every population — powered by AI and pharmacogenomics.*

</div>

---

## 🎯 Problem Statement

Adverse Drug Reactions (ADRs) are the **4th leading cause of death** in the US, with ~100,000 deaths and $528 billion in costs annually. While pharmacogenomic variants are known to affect drug metabolism for 200+ drugs, two critical gaps remain:

1. **Reactive monitoring**: Current systems detect ADRs *after* patients are harmed, not before
2. **Population inequity**: Most pharmacogenomic research is based on European-ancestry data, leaving other populations at higher risk

**PharmacoSafe** addresses both gaps by combining ML-driven ADR prediction with fairness auditing — wrapped in a stunning, interactive web interface that supports patient data upload.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 💊 **Drug-Gene Interaction Engine** | Maps 8 pharmacogenes × 15 drugs with CPIC-aligned dosing guidelines |
| 🧠 **ML ADR Predictor** | Gradient Boosting models with calibrated probabilities per drug |
| 📤 **Data Upload** | Drag & drop CSV/JSON patient data with auto-parsing and validation |
| ✍️ **Manual Entry** | Interactive form with gene phenotype selectors and clinical inputs |
| 👤 **Demo Patients** | 4 pre-loaded clinical scenarios showcasing high-risk gene-drug pairs |
| 🔍 **SHAP Explainability** | Per-patient waterfall charts explaining why a prediction was made |
| ⚖️ **Fairness Auditing** | Demographic parity, equalized odds, and calibration across 5 populations |
| 🚨 **Bias Detection** | Automated intersectional bias scanning with severity classification |
| 📋 **Clinical Recommendations** | Dosing guidance, monitoring plans, alternative drug suggestions |
| 🖥️ **Animated Web Interface** | Dark mode glassmorphism UI with particle backgrounds and animated charts |

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     PharmacoSafe Architecture                        │
├──────────────┬──────────────┬──────────────┬──────────────┬──────────┤
│   Frontend   │   FastAPI    │   ML Models  │  Pharma      │ Fairness │
│              │              │              │  Engine      │          │
│  Particles   │  /predict    │  ADR         │  Gene-Drug   │  Auditor │
│  Upload      │  /upload     │  Predictor   │  Mapper      │  Bias    │
│  Charts      │  /drugs      │  Ensemble    │  Variant     │  Detector│
│  Animations  │  /fairness   │  SHAP        │  Parser      │  Equity  │
│  Risk Gauge  │  /demo       │  Trainer     │  Drug DB     │  Reports │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/ShriyaditaSrinivaas/PharmacoSafe.git
cd PharmacoSafe

# Install dependencies
pip install -r requirements.txt
```

### Run the Full Pipeline

```bash
# 1. Generate synthetic pharmacogenomic data (3000 patients, 5 populations)
python scripts/generate_data.py

# 2. Train ADR prediction models for 8 priority drugs
python scripts/train_models.py

# 3. Run fairness audit across populations
python scripts/run_fairness_audit.py

# 4. Launch the web application
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000** in your browser.

Or use the Makefile:

```bash
make install    # Install dependencies
make pipeline   # Run steps 1-3
make server     # Launch web app
make test       # Run tests
```

## 🖥️ Web Interface

The frontend is a single-page application with:

- **🌌 Animated particle background** — floating molecules with mouse interaction
- **✨ Glassmorphism cards** — frosted glass effect with hover glow
- **📤 Drag & drop upload** — CSV/JSON file parsing with validation
- **✍️ Manual entry form** — gene phenotype selectors + clinical inputs
- **📊 Animated risk gauge** — 0-100% with color gradient
- **🔍 SHAP waterfall chart** — interactive per-patient explanations
- **⚖️ Fairness dashboard** — population comparison charts
- **💊 Drug database** — searchable with pharmacogenomic profiles

## 📊 Pharmacogenes Covered

| Gene | % of Drugs Metabolized | Key Clinical Impact |
|------|----------------------|---------------------|
| CYP2D6 | ~25% | Codeine toxicity, tamoxifen efficacy |
| CYP2C19 | ~15% | Clopidogrel activation failure |
| CYP2C9 | ~10% | Warfarin bleeding risk |
| CYP3A4 | ~50% | Statin myopathy, tacrolimus toxicity |
| DPYD | Fluoropyrimidines | Fatal 5-FU toxicity |
| TPMT | Thiopurines | Life-threatening myelosuppression |
| UGT1A1 | Irinotecan, atazanavir | Severe neutropenia |
| VKORC1 | Warfarin target | Warfarin dose sensitivity |

## 🗂️ Project Structure

```
PharmacoSafe/
├── pharmacosafe/                    # Core Python package
│   ├── config.py                    # Configuration + drug database
│   ├── data/
│   │   ├── generator.py            # Synthetic pharmacogenomic data
│   │   └── preprocessor.py         # Data validation & encoding
│   ├── models/
│   │   ├── adr_predictor.py        # Gradient Boosting ADR predictor
│   │   ├── dosing_recommender.py   # CPIC-aligned dosing engine
│   │   ├── ensemble.py             # Stacking ensemble
│   │   └── trainer.py              # Training pipeline
│   ├── pharmaco/
│   │   ├── gene_drug_mapper.py     # Gene → drug interaction mapping
│   │   ├── variant_parser.py       # CSV/JSON file parser
│   │   └── drug_database.py        # Drug-gene interaction DB
│   ├── interpretability/
│   │   ├── shap_explainer.py       # SHAP explanations
│   │   └── clinical_report.py      # Report generator
│   └── fairness/
│       ├── auditor.py              # Fairness metrics engine
│       └── bias_detector.py        # Bias detection
├── api/
│   └── main.py                     # FastAPI application
├── frontend/                        # Animated web interface
│   ├── index.html                  # Single-page app
│   ├── css/                        # Design system + animations
│   └── js/                         # App logic + particles + charts
├── scripts/                        # Pipeline scripts
├── tests/                          # Test suite
├── docs/                           # Methodology documentation
├── .github/workflows/ci.yml       # CI/CD pipeline
├── pyproject.toml
├── requirements.txt
└── Makefile
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=pharmacosafe --cov-report=term-missing
```

## 📚 Clinical Context

This project addresses the critical gap between pharmacogenomic knowledge and clinical practice. While CPIC guidelines exist for many drug-gene pairs, adoption remains low — fewer than 5% of patients receive pre-treatment pharmacogenomic testing. PharmacoSafe demonstrates how AI can bridge this gap by:

1. Integrating genetic and clinical data into a unified risk score
2. Providing interpretable explanations clinicians can trust
3. Auditing for population-level disparities in prediction accuracy
4. Offering actionable dosing recommendations aligned with CPIC guidelines

**Disclaimer**: This is a research demonstration using synthetic data. It is not intended for clinical use. All medical decisions should be made by qualified healthcare providers.

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 👤 Author

**Shriyadita Srinivaas**

---

<div align="center">
<i>Building equitable drug safety for every genome 💊🧬</i>
</div>
