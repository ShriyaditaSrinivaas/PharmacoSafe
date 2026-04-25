"""Tests for the gene-drug mapper and variant parser."""

import pytest
import sys
sys.path.insert(0, ".")

from pharmacosafe.pharmaco.gene_drug_mapper import GeneDrugMapper
from pharmacosafe.pharmaco.variant_parser import VariantParser
from pharmacosafe.pharmaco.drug_database import DrugDatabase


class TestGeneDrugMapper:

    def setup_method(self):
        self.mapper = GeneDrugMapper()

    def test_patient_profile_has_all_genes(self):
        patient = {"CYP2D6_phenotype": "Poor", "CYP2C19_phenotype": "Normal"}
        profile = self.mapper.get_patient_profile(patient)
        assert "CYP2D6" in profile["genes"]
        assert profile["genes"]["CYP2D6"]["phenotype"] == "Poor"

    def test_high_risk_drugs_detected(self):
        patient = {"CYP2D6_phenotype": "Ultra-rapid"}
        profile = self.mapper.get_patient_profile(patient)
        assert len(profile["drug_interactions"]) > 0

    def test_warfarin_recommendations(self):
        patient = {"CYP2C9_phenotype": "Poor", "VKORC1_phenotype": "High Sensitivity"}
        recs = self.mapper.get_drug_recommendations(patient, "warfarin")
        assert recs["overall_risk"] == "high"
        assert len(recs["dosing_recommendations"]) > 0

    def test_drug_search(self):
        results = self.mapper.search_drugs("anticoagulant")
        assert len(results) >= 1
        assert any(r["drug_id"] == "warfarin" for r in results)


class TestVariantParser:

    def setup_method(self):
        self.parser = VariantParser()

    def test_parse_csv(self):
        csv_data = "age,sex,CYP2D6_phenotype\n45,Male,Poor"
        result = self.parser.parse_csv(csv_data)
        assert result["n_patients"] == 1
        assert result["patients"][0]["age"] == 45

    def test_parse_json_single(self):
        json_data = '{"age": 30, "sex": "Female", "CYP2C19_phenotype": "Intermediate"}'
        result = self.parser.parse_json(json_data)
        assert result["n_patients"] == 1

    def test_parse_json_array(self):
        json_data = '[{"age": 30}, {"age": 40}]'
        result = self.parser.parse_json(json_data)
        assert result["n_patients"] == 2

    def test_normalize_phenotype_abbreviations(self):
        result = self.parser._normalize_phenotype("PM", "CYP2D6")
        assert result == "Poor"
        result = self.parser._normalize_phenotype("UM", "CYP2D6")
        assert result == "Ultra-rapid"

    def test_auto_detect_format(self):
        csv_data = "age,sex\n45,Male"
        result = self.parser.parse_auto(csv_data, "test.csv")
        assert result["format"] == "csv"


class TestDrugDatabase:

    def setup_method(self):
        self.db = DrugDatabase()

    def test_get_all_drugs(self):
        drugs = self.db.get_all_drugs()
        assert len(drugs) >= 10

    def test_get_drug(self):
        drug = self.db.get_drug("warfarin")
        assert drug is not None
        assert drug["name"] == "Warfarin"

    def test_search(self):
        results = self.db.search("cancer")
        assert len(results) >= 1

    def test_drugs_for_gene(self):
        drugs = self.db.get_drugs_for_gene("CYP2D6")
        assert len(drugs) >= 2

    def test_statistics(self):
        stats = self.db.get_statistics()
        assert stats["n_drugs"] >= 10
        assert stats["n_genes"] >= 8
