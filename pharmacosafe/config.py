"""
Configuration management for PharmacoSafe.
Centralizes all paths, hyperparameters, and constants.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List


# ── Project Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Ensure directories exist
for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── Populations ────────────────────────────────────────────────────────────
POPULATIONS = ["EUR", "AFR", "EAS", "SAS", "AMR"]
POPULATION_NAMES = {
    "EUR": "European",
    "AFR": "African",
    "EAS": "East Asian",
    "SAS": "South Asian",
    "AMR": "Admixed American",
}
POPULATION_PROPORTIONS = {
    "EUR": 0.30,
    "AFR": 0.25,
    "EAS": 0.20,
    "SAS": 0.15,
    "AMR": 0.10,
}


# ── Pharmacogenes ──────────────────────────────────────────────────────────
PHARMACOGENES = {
    "CYP2D6": {
        "description": "Cytochrome P450 2D6 — metabolizes ~25% of all drugs",
        "phenotypes": ["Poor", "Intermediate", "Normal", "Rapid", "Ultra-rapid"],
        "population_frequencies": {
            "EUR": [0.07, 0.15, 0.55, 0.18, 0.05],
            "AFR": [0.03, 0.10, 0.40, 0.27, 0.20],
            "EAS": [0.01, 0.08, 0.65, 0.22, 0.04],
            "SAS": [0.04, 0.12, 0.58, 0.20, 0.06],
            "AMR": [0.05, 0.13, 0.52, 0.22, 0.08],
        },
    },
    "CYP2C19": {
        "description": "Cytochrome P450 2C19 — activates clopidogrel, metabolizes PPIs",
        "phenotypes": ["Poor", "Intermediate", "Normal", "Rapid", "Ultra-rapid"],
        "population_frequencies": {
            "EUR": [0.03, 0.18, 0.58, 0.17, 0.04],
            "AFR": [0.04, 0.15, 0.50, 0.22, 0.09],
            "EAS": [0.14, 0.35, 0.40, 0.09, 0.02],
            "SAS": [0.10, 0.28, 0.45, 0.13, 0.04],
            "AMR": [0.05, 0.20, 0.52, 0.18, 0.05],
        },
    },
    "CYP2C9": {
        "description": "Cytochrome P450 2C9 — metabolizes warfarin, NSAIDs, phenytoin",
        "phenotypes": ["Poor", "Intermediate", "Normal"],
        "population_frequencies": {
            "EUR": [0.03, 0.25, 0.72],
            "AFR": [0.01, 0.08, 0.91],
            "EAS": [0.01, 0.06, 0.93],
            "SAS": [0.02, 0.15, 0.83],
            "AMR": [0.02, 0.18, 0.80],
        },
    },
    "CYP3A4": {
        "description": "Cytochrome P450 3A4 — metabolizes ~50% of all drugs",
        "phenotypes": ["Poor", "Intermediate", "Normal"],
        "population_frequencies": {
            "EUR": [0.02, 0.12, 0.86],
            "AFR": [0.04, 0.18, 0.78],
            "EAS": [0.01, 0.08, 0.91],
            "SAS": [0.02, 0.10, 0.88],
            "AMR": [0.03, 0.14, 0.83],
        },
    },
    "DPYD": {
        "description": "Dihydropyrimidine dehydrogenase — metabolizes fluoropyrimidines",
        "phenotypes": ["Poor", "Intermediate", "Normal"],
        "population_frequencies": {
            "EUR": [0.01, 0.08, 0.91],
            "AFR": [0.02, 0.12, 0.86],
            "EAS": [0.005, 0.04, 0.955],
            "SAS": [0.01, 0.06, 0.93],
            "AMR": [0.01, 0.07, 0.92],
        },
    },
    "TPMT": {
        "description": "Thiopurine methyltransferase — metabolizes thiopurines",
        "phenotypes": ["Poor", "Intermediate", "Normal"],
        "population_frequencies": {
            "EUR": [0.003, 0.10, 0.897],
            "AFR": [0.005, 0.08, 0.915],
            "EAS": [0.002, 0.05, 0.948],
            "SAS": [0.003, 0.07, 0.927],
            "AMR": [0.004, 0.09, 0.906],
        },
    },
    "UGT1A1": {
        "description": "UDP-glucuronosyltransferase — metabolizes irinotecan, atazanavir",
        "phenotypes": ["Poor", "Intermediate", "Normal"],
        "population_frequencies": {
            "EUR": [0.10, 0.30, 0.60],
            "AFR": [0.15, 0.35, 0.50],
            "EAS": [0.08, 0.28, 0.64],
            "SAS": [0.12, 0.32, 0.56],
            "AMR": [0.11, 0.31, 0.58],
        },
    },
    "VKORC1": {
        "description": "Vitamin K epoxide reductase — warfarin target",
        "phenotypes": ["High Sensitivity", "Normal Sensitivity", "Low Sensitivity"],
        "population_frequencies": {
            "EUR": [0.35, 0.50, 0.15],
            "AFR": [0.10, 0.55, 0.35],
            "EAS": [0.85, 0.13, 0.02],
            "SAS": [0.45, 0.42, 0.13],
            "AMR": [0.40, 0.45, 0.15],
        },
    },
}


# ── Drug Database ──────────────────────────────────────────────────────────
DRUG_DATABASE = {
    "warfarin": {
        "name": "Warfarin",
        "class": "Anticoagulant",
        "indication": "Blood clot prevention",
        "key_genes": ["CYP2C9", "VKORC1"],
        "common_adrs": ["Bleeding", "Bruising", "Hemorrhage", "Skin necrosis"],
        "severe_adr_rate": 0.15,
        "description": "Narrow therapeutic index anticoagulant. Dose highly dependent on CYP2C9 and VKORC1 genotype.",
    },
    "clopidogrel": {
        "name": "Clopidogrel",
        "class": "Antiplatelet",
        "indication": "Prevention of heart attack and stroke",
        "key_genes": ["CYP2C19"],
        "common_adrs": ["Bleeding", "Rash", "Diarrhea", "Thrombotic thrombocytopenic purpura"],
        "severe_adr_rate": 0.10,
        "description": "Prodrug requiring CYP2C19 activation. Poor metabolizers have reduced efficacy and increased cardiovascular risk.",
    },
    "codeine": {
        "name": "Codeine",
        "class": "Opioid analgesic",
        "indication": "Pain relief, cough suppression",
        "key_genes": ["CYP2D6"],
        "common_adrs": ["Respiratory depression", "Nausea", "Sedation", "Constipation"],
        "severe_adr_rate": 0.12,
        "description": "Prodrug converted to morphine by CYP2D6. Ultra-rapid metabolizers at risk for toxicity; poor metabolizers get no benefit.",
    },
    "tamoxifen": {
        "name": "Tamoxifen",
        "class": "Selective estrogen receptor modulator",
        "indication": "Breast cancer treatment and prevention",
        "key_genes": ["CYP2D6"],
        "common_adrs": ["Hot flashes", "Blood clots", "Endometrial cancer", "Fatigue"],
        "severe_adr_rate": 0.08,
        "description": "Converted to active metabolite endoxifen by CYP2D6. Poor metabolizers may have reduced efficacy.",
    },
    "fluorouracil": {
        "name": "5-Fluorouracil (5-FU)",
        "class": "Antimetabolite chemotherapy",
        "indication": "Colorectal, breast, and head/neck cancers",
        "key_genes": ["DPYD"],
        "common_adrs": ["Severe mucositis", "Neutropenia", "Diarrhea", "Hand-foot syndrome", "Death"],
        "severe_adr_rate": 0.20,
        "description": "DPYD-deficient patients at extreme risk of fatal toxicity. Pre-treatment genotyping recommended by CPIC.",
    },
    "azathioprine": {
        "name": "Azathioprine",
        "class": "Immunosuppressant",
        "indication": "Organ transplant rejection, autoimmune diseases",
        "key_genes": ["TPMT"],
        "common_adrs": ["Myelosuppression", "Leukopenia", "Hepatotoxicity", "Pancreatitis"],
        "severe_adr_rate": 0.14,
        "description": "TPMT-deficient patients at high risk of life-threatening myelosuppression. Dose reduction or alternative therapy required.",
    },
    "irinotecan": {
        "name": "Irinotecan",
        "class": "Topoisomerase inhibitor chemotherapy",
        "indication": "Colorectal cancer",
        "key_genes": ["UGT1A1"],
        "common_adrs": ["Severe diarrhea", "Neutropenia", "Nausea", "Alopecia"],
        "severe_adr_rate": 0.18,
        "description": "UGT1A1 poor metabolizers at increased risk of severe neutropenia and diarrhea. Dose reduction recommended.",
    },
    "simvastatin": {
        "name": "Simvastatin",
        "class": "Statin",
        "indication": "Cholesterol reduction",
        "key_genes": ["CYP3A4"],
        "common_adrs": ["Myopathy", "Rhabdomyolysis", "Liver enzyme elevation", "Muscle pain"],
        "severe_adr_rate": 0.06,
        "description": "CYP3A4 interactions can increase statin levels dramatically, raising risk of rhabdomyolysis.",
    },
    "omeprazole": {
        "name": "Omeprazole",
        "class": "Proton pump inhibitor",
        "indication": "GERD, peptic ulcers",
        "key_genes": ["CYP2C19"],
        "common_adrs": ["Headache", "C. diff infection", "Bone fractures", "Magnesium deficiency"],
        "severe_adr_rate": 0.04,
        "description": "CYP2C19 rapid metabolizers may need higher doses for efficacy. Poor metabolizers have increased drug exposure.",
    },
    "tramadol": {
        "name": "Tramadol",
        "class": "Opioid analgesic",
        "indication": "Moderate to severe pain",
        "key_genes": ["CYP2D6"],
        "common_adrs": ["Seizures", "Serotonin syndrome", "Respiratory depression", "Nausea"],
        "severe_adr_rate": 0.09,
        "description": "Like codeine, partially activated by CYP2D6. Ultra-rapid metabolizers at risk; poor metabolizers may lack efficacy.",
    },
    "tacrolimus": {
        "name": "Tacrolimus",
        "class": "Calcineurin inhibitor",
        "indication": "Organ transplant rejection prevention",
        "key_genes": ["CYP3A4"],
        "common_adrs": ["Nephrotoxicity", "Neurotoxicity", "Diabetes", "Hypertension"],
        "severe_adr_rate": 0.16,
        "description": "Narrow therapeutic index. CYP3A4/5 genotype significantly affects blood levels and toxicity risk.",
    },
    "mercaptopurine": {
        "name": "Mercaptopurine (6-MP)",
        "class": "Antimetabolite",
        "indication": "Acute lymphoblastic leukemia",
        "key_genes": ["TPMT"],
        "common_adrs": ["Myelosuppression", "Hepatotoxicity", "Immunosuppression", "Nausea"],
        "severe_adr_rate": 0.15,
        "description": "TPMT-deficient patients require 10% of standard dose to avoid fatal myelosuppression.",
    },
    "atazanavir": {
        "name": "Atazanavir",
        "class": "Protease inhibitor",
        "indication": "HIV treatment",
        "key_genes": ["UGT1A1"],
        "common_adrs": ["Jaundice", "Hyperbilirubinemia", "Nephrolithiasis", "Rash"],
        "severe_adr_rate": 0.07,
        "description": "UGT1A1 poor metabolizers at increased risk of hyperbilirubinemia and jaundice.",
    },
    "capecitabine": {
        "name": "Capecitabine",
        "class": "Antimetabolite chemotherapy",
        "indication": "Breast and colorectal cancer",
        "key_genes": ["DPYD"],
        "common_adrs": ["Hand-foot syndrome", "Severe diarrhea", "Neutropenia", "Cardiotoxicity"],
        "severe_adr_rate": 0.19,
        "description": "Oral fluoropyrimidine prodrug. Same DPYD-related risks as 5-FU. Pre-treatment testing critical.",
    },
    "phenytoin": {
        "name": "Phenytoin",
        "class": "Anticonvulsant",
        "indication": "Epilepsy, seizure prevention",
        "key_genes": ["CYP2C9"],
        "common_adrs": ["Ataxia", "Nystagmus", "Gingival hyperplasia", "Steven-Johnson syndrome"],
        "severe_adr_rate": 0.11,
        "description": "CYP2C9 poor metabolizers at risk of phenytoin toxicity. Dose adjustment recommended by CPIC.",
    },
}


# ── Model Configuration ───────────────────────────────────────────────────
@dataclass
class ModelConfig:
    """Hyperparameters for ADR prediction models."""
    n_estimators: int = 200
    max_depth: int = 6
    learning_rate: float = 0.1
    min_child_weight: int = 5
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    random_state: int = 42
    cv_folds: int = 5
    test_size: float = 0.2
    calibration_method: str = "isotonic"


@dataclass
class DataConfig:
    """Configuration for synthetic data generation."""
    n_samples: int = 3000
    n_populations: int = 5
    random_state: int = 42
    age_range: tuple = (18, 90)
    weight_range_kg: tuple = (45, 130)


@dataclass
class FairnessConfig:
    """Configuration for fairness auditing."""
    demographic_parity_threshold: float = 0.10
    equalized_odds_threshold: float = 0.10
    calibration_threshold: float = 0.10
    severity_levels: Dict[str, float] = field(default_factory=lambda: {
        "negligible": 0.05,
        "low": 0.10,
        "moderate": 0.20,
        "high": 1.0,
    })
    protected_attributes: List[str] = field(default_factory=lambda: [
        "population", "sex", "age_group"
    ])
