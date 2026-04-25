"""
Synthetic pharmacogenomic data generator.
Generates biologically plausible patient data with pharmacogene metabolizer
phenotypes, clinical features, and ADR outcomes across 5 populations.
"""

import numpy as np
import pandas as pd
from typing import Optional

from pharmacosafe.config import (
    PHARMACOGENES,
    DRUG_DATABASE,
    POPULATIONS,
    POPULATION_PROPORTIONS,
    DataConfig,
    DATA_DIR,
)


class PharmacogenomicDataGenerator:
    """Generates synthetic patient data with pharmacogenomic profiles and ADR outcomes."""

    def __init__(self, config: Optional[DataConfig] = None):
        self.config = config or DataConfig()
        self.rng = np.random.RandomState(self.config.random_state)

    def generate(self) -> pd.DataFrame:
        """Generate the full synthetic dataset."""
        n = self.config.n_samples

        # ── Assign populations ─────────────────────────────────────────
        populations = self.rng.choice(
            POPULATIONS,
            size=n,
            p=[POPULATION_PROPORTIONS[p] for p in POPULATIONS],
        )

        # ── Clinical features ──────────────────────────────────────────
        ages = self.rng.randint(
            self.config.age_range[0], self.config.age_range[1] + 1, size=n
        )
        sexes = self.rng.choice(["Male", "Female"], size=n, p=[0.48, 0.52])

        # Weight varies by population and sex
        base_weight = {
            "EUR": 78, "AFR": 82, "EAS": 65, "SAS": 68, "AMR": 75,
        }
        weights = np.array([
            self.rng.normal(
                base_weight[pop] + (-5 if sex == "Female" else 5),
                12,
            )
            for pop, sex in zip(populations, sexes)
        ]).clip(self.config.weight_range_kg[0], self.config.weight_range_kg[1])

        # Kidney function (eGFR mL/min/1.73m²)
        egfr = self.rng.normal(90, 20, size=n).clip(15, 140)
        # Age-related decline
        egfr -= np.maximum(0, (ages - 40) * 0.5)
        egfr = egfr.clip(15, 140)

        # Liver function (ALT, U/L)
        alt = self.rng.lognormal(3.0, 0.4, size=n).clip(10, 200)

        # Number of co-medications (polypharmacy)
        n_comedications = self.rng.poisson(2.5, size=n).clip(0, 15)
        # Older patients tend to have more medications
        n_comedications = (n_comedications + np.maximum(0, (ages - 60) // 10)).clip(0, 15)

        # BMI
        heights_m = np.where(
            sexes == "Male",
            self.rng.normal(1.75, 0.08, size=n),
            self.rng.normal(1.62, 0.07, size=n),
        ).clip(1.40, 2.10)
        bmi = weights / (heights_m ** 2)

        # Smoking status
        smoking = self.rng.choice(
            ["Never", "Former", "Current"], size=n, p=[0.55, 0.30, 0.15]
        )

        # Diabetes flag (higher in certain populations)
        diabetes_prob = {
            "EUR": 0.10, "AFR": 0.13, "EAS": 0.11, "SAS": 0.18, "AMR": 0.14,
        }
        diabetes = np.array([
            self.rng.binomial(1, diabetes_prob[pop]) for pop in populations
        ])

        # ── Pharmacogene phenotypes ────────────────────────────────────
        gene_data = {}
        for gene_name, gene_info in PHARMACOGENES.items():
            phenotypes = gene_info["phenotypes"]
            gene_phenotypes = []
            for pop in populations:
                freqs = gene_info["population_frequencies"][pop]
                phenotype = self.rng.choice(phenotypes, p=freqs)
                gene_phenotypes.append(phenotype)
            gene_data[f"{gene_name}_phenotype"] = gene_phenotypes

        # ── Assemble base DataFrame ────────────────────────────────────
        df = pd.DataFrame({
            "patient_id": [f"PS-{i:05d}" for i in range(n)],
            "population": populations,
            "age": ages,
            "sex": sexes,
            "weight_kg": np.round(weights, 1),
            "height_m": np.round(heights_m, 2),
            "bmi": np.round(bmi, 1),
            "egfr": np.round(egfr, 1),
            "alt_u_l": np.round(alt, 1),
            "n_comedications": n_comedications.astype(int),
            "smoking_status": smoking,
            "diabetes": diabetes,
            **gene_data,
        })

        # ── Generate ADR outcomes for each drug ────────────────────────
        for drug_id, drug_info in DRUG_DATABASE.items():
            adr_risk = self._calculate_adr_risk(df, drug_id, drug_info)
            adr_occurred = (self.rng.random(n) < adr_risk).astype(int)
            df[f"adr_{drug_id}"] = adr_occurred
            df[f"adr_risk_{drug_id}"] = np.round(adr_risk, 4)

        # ── Age groups ─────────────────────────────────────────────────
        df["age_group"] = pd.cut(
            df["age"],
            bins=[0, 30, 50, 65, 100],
            labels=["Young", "Middle", "Senior", "Elderly"],
        ).astype(str)

        return df

    def _calculate_adr_risk(
        self, df: pd.DataFrame, drug_id: str, drug_info: dict
    ) -> np.ndarray:
        """Calculate ADR probability for each patient for a given drug."""
        n = len(df)
        base_rate = drug_info["severe_adr_rate"]

        # Start with base rate
        risk = np.full(n, base_rate)

        # ── Gene-based risk modifiers ──────────────────────────────────
        for gene in drug_info["key_genes"]:
            phenotype_col = f"{gene}_phenotype"
            if phenotype_col not in df.columns:
                continue

            phenotypes = df[phenotype_col].values

            if gene == "VKORC1":
                # VKORC1 affects warfarin sensitivity differently
                modifiers = {
                    "High Sensitivity": 2.5,
                    "Normal Sensitivity": 1.0,
                    "Low Sensitivity": 0.5,
                }
            else:
                # Standard metabolizer phenotype risk modifiers
                modifiers = {
                    "Poor": 3.0,
                    "Intermediate": 1.8,
                    "Normal": 1.0,
                    "Rapid": 0.7,
                    "Ultra-rapid": 2.2,  # Toxicity risk for prodrugs
                }

            for phenotype, modifier in modifiers.items():
                mask = phenotypes == phenotype
                risk[mask] *= modifier

        # ── Clinical feature modifiers ─────────────────────────────────
        # Age: elderly patients have higher ADR risk
        risk *= 1 + np.maximum(0, (df["age"].values - 65)) * 0.01

        # Kidney function: impaired clearance increases risk
        risk *= np.where(df["egfr"].values < 60, 1.5, 1.0)
        risk *= np.where(df["egfr"].values < 30, 2.0, 1.0)

        # Liver function: elevated ALT suggests impaired metabolism
        risk *= np.where(df["alt_u_l"].values > 80, 1.4, 1.0)

        # Polypharmacy: drug interactions increase ADR risk
        risk *= 1 + df["n_comedications"].values * 0.04

        # BMI extremes
        risk *= np.where((df["bmi"].values < 18.5) | (df["bmi"].values > 35), 1.3, 1.0)

        # Add noise
        noise = self.rng.normal(0, 0.02, size=n)
        risk = (risk + noise).clip(0.01, 0.95)

        return risk

    def save(self, df: pd.DataFrame, filename: str = "pharmacogenomic_data.csv"):
        """Save dataset to CSV."""
        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False)
        return filepath
