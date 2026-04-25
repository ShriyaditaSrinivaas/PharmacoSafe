"""Tests for the pharmacogenomic data generator."""

import pytest
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, ".")

from pharmacosafe.data.generator import PharmacogenomicDataGenerator
from pharmacosafe.config import DataConfig, POPULATIONS, PHARMACOGENES, DRUG_DATABASE


class TestPharmacogenomicDataGenerator:

    def setup_method(self):
        self.config = DataConfig(n_samples=200, random_state=42)
        self.generator = PharmacogenomicDataGenerator(self.config)
        self.df = self.generator.generate()

    def test_correct_sample_count(self):
        assert len(self.df) == 200

    def test_all_populations_present(self):
        for pop in POPULATIONS:
            assert pop in self.df["population"].values

    def test_patient_ids_unique(self):
        assert self.df["patient_id"].nunique() == len(self.df)

    def test_age_range(self):
        assert self.df["age"].min() >= 18
        assert self.df["age"].max() <= 90

    def test_pharmacogene_columns_exist(self):
        for gene in PHARMACOGENES:
            assert f"{gene}_phenotype" in self.df.columns

    def test_adr_columns_exist(self):
        for drug_id in DRUG_DATABASE:
            assert f"adr_{drug_id}" in self.df.columns
            assert f"adr_risk_{drug_id}" in self.df.columns

    def test_adr_values_binary(self):
        for drug_id in DRUG_DATABASE:
            assert set(self.df[f"adr_{drug_id}"].unique()).issubset({0, 1})

    def test_adr_risk_range(self):
        for drug_id in list(DRUG_DATABASE.keys())[:3]:
            risks = self.df[f"adr_risk_{drug_id}"]
            assert risks.min() >= 0
            assert risks.max() <= 1

    def test_sex_values(self):
        assert set(self.df["sex"].unique()).issubset({"Male", "Female"})

    def test_reproducibility(self):
        gen2 = PharmacogenomicDataGenerator(self.config)
        df2 = gen2.generate()
        pd.testing.assert_frame_equal(self.df, df2)
