"""
Gene-Drug Mapper for PharmacoSafe.
Maps pharmacogenomic variants to metabolizer phenotypes and drug interactions.
Provides CPIC-aligned clinical recommendations.
"""

from typing import Dict, List, Optional
from pharmacosafe.config import PHARMACOGENES, DRUG_DATABASE


class GeneDrugMapper:
    """Maps gene variants to metabolizer phenotypes and generates drug interaction profiles."""

    # ── Metabolizer impact descriptions ────────────────────────────────
    METABOLIZER_IMPACTS = {
        "Poor": {
            "enzyme_activity": "Absent or minimal",
            "drug_level_effect": "Significantly increased drug levels",
            "clinical_impact": "High risk of toxicity for drugs metabolized by this enzyme",
            "prodrug_impact": "No activation — drug may be ineffective",
            "risk_level": "high",
        },
        "Intermediate": {
            "enzyme_activity": "Reduced (~50%)",
            "drug_level_effect": "Moderately increased drug levels",
            "clinical_impact": "Increased risk of adverse effects; dose reduction may be needed",
            "prodrug_impact": "Reduced activation — may have decreased efficacy",
            "risk_level": "moderate",
        },
        "Normal": {
            "enzyme_activity": "Normal (reference)",
            "drug_level_effect": "Standard drug levels expected",
            "clinical_impact": "Standard dosing appropriate",
            "prodrug_impact": "Normal activation expected",
            "risk_level": "low",
        },
        "Rapid": {
            "enzyme_activity": "Increased (~150%)",
            "drug_level_effect": "Decreased drug levels",
            "clinical_impact": "May need higher doses for efficacy",
            "prodrug_impact": "Enhanced activation — monitor for increased effect",
            "risk_level": "moderate",
        },
        "Ultra-rapid": {
            "enzyme_activity": "Markedly increased (>200%)",
            "drug_level_effect": "Substantially decreased drug levels",
            "clinical_impact": "Standard doses may be ineffective",
            "prodrug_impact": "Excessive activation — HIGH risk of toxicity",
            "risk_level": "high",
        },
        "High Sensitivity": {
            "enzyme_activity": "High sensitivity to warfarin",
            "drug_level_effect": "Lower dose required",
            "clinical_impact": "High bleeding risk at standard doses",
            "prodrug_impact": "N/A",
            "risk_level": "high",
        },
        "Normal Sensitivity": {
            "enzyme_activity": "Normal sensitivity",
            "drug_level_effect": "Standard dose expected",
            "clinical_impact": "Standard dosing appropriate",
            "prodrug_impact": "N/A",
            "risk_level": "low",
        },
        "Low Sensitivity": {
            "enzyme_activity": "Low sensitivity / resistance",
            "drug_level_effect": "Higher dose may be required",
            "clinical_impact": "May need increased dose for therapeutic effect",
            "prodrug_impact": "N/A",
            "risk_level": "moderate",
        },
    }

    # ── Dosing recommendations ─────────────────────────────────────────
    DOSING_GUIDELINES = {
        "warfarin": {
            ("CYP2C9", "Poor"): "Reduce dose by 50-80%. Start at 1-2 mg/day.",
            ("CYP2C9", "Intermediate"): "Reduce dose by 20-40%. Start at 2-3 mg/day.",
            ("CYP2C9", "Normal"): "Standard dosing (2-5 mg/day). Titrate to INR.",
            ("VKORC1", "High Sensitivity"): "Reduce dose by 25-50%. Enhanced sensitivity.",
            ("VKORC1", "Normal Sensitivity"): "Standard dosing.",
            ("VKORC1", "Low Sensitivity"): "May require higher doses (5-7 mg/day).",
        },
        "clopidogrel": {
            ("CYP2C19", "Poor"): "AVOID clopidogrel. Use prasugrel or ticagrelor instead.",
            ("CYP2C19", "Intermediate"): "Consider alternative antiplatelet or higher dose.",
            ("CYP2C19", "Normal"): "Standard 75 mg/day dosing.",
            ("CYP2C19", "Rapid"): "Standard dosing. Good activation expected.",
            ("CYP2C19", "Ultra-rapid"): "Standard dosing. Excellent activation.",
        },
        "codeine": {
            ("CYP2D6", "Poor"): "AVOID codeine. No analgesic effect. Use non-opioid alternative.",
            ("CYP2D6", "Intermediate"): "Reduced efficacy. Consider alternative analgesic.",
            ("CYP2D6", "Normal"): "Standard dosing.",
            ("CYP2D6", "Ultra-rapid"): "AVOID codeine. HIGH risk of respiratory depression and death.",
        },
        "fluorouracil": {
            ("DPYD", "Poor"): "CONTRAINDICATED. Fatal toxicity risk. Use alternative chemotherapy.",
            ("DPYD", "Intermediate"): "Reduce dose by 50%. Close monitoring required.",
            ("DPYD", "Normal"): "Standard dosing per protocol.",
        },
        "azathioprine": {
            ("TPMT", "Poor"): "Reduce dose to 10% of standard. Life-threatening myelosuppression risk.",
            ("TPMT", "Intermediate"): "Reduce dose by 30-50%. Monitor CBC weekly.",
            ("TPMT", "Normal"): "Standard dosing. Monitor CBC per protocol.",
        },
    }

    def get_patient_profile(self, patient_data: dict) -> dict:
        """
        Generate a complete pharmacogenomic profile for a patient.

        Args:
            patient_data: Dict with gene phenotype values

        Returns:
            Comprehensive pharmacogenomic profile
        """
        profile = {
            "genes": {},
            "drug_interactions": [],
            "high_risk_drugs": [],
            "safe_drugs": [],
        }

        # Process each gene
        for gene_name, gene_info in PHARMACOGENES.items():
            phenotype_key = f"{gene_name}_phenotype"
            phenotype = patient_data.get(phenotype_key, "Normal")

            impact = self.METABOLIZER_IMPACTS.get(phenotype, {})
            profile["genes"][gene_name] = {
                "phenotype": phenotype,
                "description": gene_info["description"],
                "enzyme_activity": impact.get("enzyme_activity", "Unknown"),
                "risk_level": impact.get("risk_level", "unknown"),
            }

        # Check drug interactions
        for drug_id, drug_info in DRUG_DATABASE.items():
            interaction = self._check_drug_interaction(patient_data, drug_id, drug_info)
            profile["drug_interactions"].append(interaction)

            if interaction["risk_level"] == "high":
                profile["high_risk_drugs"].append(interaction)
            elif interaction["risk_level"] == "low":
                profile["safe_drugs"].append(interaction)

        return profile

    def get_drug_recommendations(self, patient_data: dict, drug_id: str) -> dict:
        """
        Get specific dosing recommendations for a patient-drug pair.

        Args:
            patient_data: Dict with gene phenotype values
            drug_id: Drug identifier

        Returns:
            Dosing recommendations and warnings
        """
        if drug_id not in DRUG_DATABASE:
            return {"error": f"Drug '{drug_id}' not found in database"}

        drug_info = DRUG_DATABASE[drug_id]
        recommendations = {
            "drug": drug_info["name"],
            "drug_class": drug_info["class"],
            "indication": drug_info["indication"],
            "gene_interactions": [],
            "dosing_recommendations": [],
            "warnings": [],
            "alternatives": [],
            "overall_risk": "low",
        }

        risk_levels = []

        for gene in drug_info["key_genes"]:
            phenotype_key = f"{gene}_phenotype"
            phenotype = patient_data.get(phenotype_key, "Normal")

            impact = self.METABOLIZER_IMPACTS.get(phenotype, {})
            risk_levels.append(impact.get("risk_level", "low"))

            gene_interaction = {
                "gene": gene,
                "phenotype": phenotype,
                "impact": impact.get("clinical_impact", "Unknown"),
                "risk_level": impact.get("risk_level", "low"),
            }
            recommendations["gene_interactions"].append(gene_interaction)

            # Get specific dosing guideline
            drug_guidelines = self.DOSING_GUIDELINES.get(drug_id, {})
            guideline = drug_guidelines.get((gene, phenotype))
            if guideline:
                recommendations["dosing_recommendations"].append({
                    "gene": gene,
                    "phenotype": phenotype,
                    "recommendation": guideline,
                })

                # Add warnings for high-risk situations
                if "AVOID" in guideline or "CONTRAINDICATED" in guideline:
                    recommendations["warnings"].append(guideline)

        # Determine overall risk
        if "high" in risk_levels:
            recommendations["overall_risk"] = "high"
        elif "moderate" in risk_levels:
            recommendations["overall_risk"] = "moderate"
        else:
            recommendations["overall_risk"] = "low"

        return recommendations

    def _check_drug_interaction(
        self, patient_data: dict, drug_id: str, drug_info: dict
    ) -> dict:
        """Check a single drug interaction for a patient."""
        interaction = {
            "drug_id": drug_id,
            "drug_name": drug_info["name"],
            "drug_class": drug_info["class"],
            "key_genes": drug_info["key_genes"],
            "risk_level": "low",
            "issues": [],
        }

        for gene in drug_info["key_genes"]:
            phenotype_key = f"{gene}_phenotype"
            phenotype = patient_data.get(phenotype_key, "Normal")
            impact = self.METABOLIZER_IMPACTS.get(phenotype, {})

            if impact.get("risk_level") == "high":
                interaction["risk_level"] = "high"
                interaction["issues"].append(
                    f"{gene} {phenotype} metabolizer: {impact.get('clinical_impact', '')}"
                )
            elif impact.get("risk_level") == "moderate" and interaction["risk_level"] != "high":
                interaction["risk_level"] = "moderate"
                interaction["issues"].append(
                    f"{gene} {phenotype} metabolizer: {impact.get('clinical_impact', '')}"
                )

        return interaction

    def search_drugs(self, query: str) -> List[dict]:
        """Search drugs by name, class, or indication."""
        query_lower = query.lower()
        results = []

        for drug_id, drug_info in DRUG_DATABASE.items():
            if (
                query_lower in drug_id.lower()
                or query_lower in drug_info["name"].lower()
                or query_lower in drug_info["class"].lower()
                or query_lower in drug_info["indication"].lower()
            ):
                results.append({
                    "drug_id": drug_id,
                    **drug_info,
                })

        return results
