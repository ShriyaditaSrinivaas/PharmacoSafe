"""
Dosing Recommender for PharmacoSafe.
Combines rule-based CPIC guidelines with ML-predicted risk
to generate personalized dosing recommendations.
"""

from typing import Dict, List, Optional
from pharmacosafe.config import DRUG_DATABASE, PHARMACOGENES
from pharmacosafe.pharmaco.gene_drug_mapper import GeneDrugMapper


class DosingRecommender:
    """Generates personalized dosing recommendations based on pharmacogenomic profile and predicted ADR risk."""

    def __init__(self):
        self.mapper = GeneDrugMapper()

    def recommend(
        self,
        patient_data: dict,
        drug_id: str,
        predicted_risk: float,
    ) -> dict:
        """
        Generate a comprehensive dosing recommendation.

        Args:
            patient_data: Patient clinical + genetic data
            drug_id: Drug identifier
            predicted_risk: ML-predicted ADR probability (0-1)

        Returns:
            Complete dosing recommendation with clinical guidance
        """
        if drug_id not in DRUG_DATABASE:
            return {"error": f"Drug '{drug_id}' not found"}

        drug_info = DRUG_DATABASE[drug_id]

        # Get gene-based recommendations
        gene_recs = self.mapper.get_drug_recommendations(patient_data, drug_id)

        # Build recommendation
        recommendation = {
            "drug": drug_info["name"],
            "drug_class": drug_info["class"],
            "predicted_risk": round(predicted_risk, 4),
            "predicted_risk_percent": round(predicted_risk * 100, 1),
            "risk_category": self._risk_category(predicted_risk),
            "action": self._determine_action(gene_recs, predicted_risk),
            "dosing_guidance": [],
            "monitoring": [],
            "alternatives": [],
            "warnings": gene_recs.get("warnings", []),
            "gene_interactions": gene_recs.get("gene_interactions", []),
        }

        # Dosing guidance
        recommendation["dosing_guidance"] = self._build_dosing_guidance(
            drug_id, patient_data, predicted_risk, gene_recs
        )

        # Monitoring recommendations
        recommendation["monitoring"] = self._build_monitoring(
            drug_id, predicted_risk, patient_data
        )

        # Alternative drugs if high risk
        if predicted_risk >= 0.5 or recommendation["action"] == "AVOID":
            recommendation["alternatives"] = self._suggest_alternatives(drug_id)

        return recommendation

    def _risk_category(self, risk: float) -> str:
        """Categorize risk level."""
        if risk >= 0.7:
            return "Critical"
        elif risk >= 0.5:
            return "High"
        elif risk >= 0.3:
            return "Moderate"
        elif risk >= 0.15:
            return "Low"
        return "Minimal"

    def _determine_action(self, gene_recs: dict, predicted_risk: float) -> str:
        """Determine the clinical action."""
        warnings = gene_recs.get("warnings", [])

        # Check for contraindications
        for w in warnings:
            if "CONTRAINDICATED" in w.upper():
                return "CONTRAINDICATED"
            if "AVOID" in w.upper():
                return "AVOID"

        if predicted_risk >= 0.7:
            return "AVOID"
        elif predicted_risk >= 0.5:
            return "USE_WITH_EXTREME_CAUTION"
        elif predicted_risk >= 0.3:
            return "DOSE_ADJUSTMENT_RECOMMENDED"
        elif predicted_risk >= 0.15:
            return "STANDARD_DOSE_WITH_MONITORING"
        return "STANDARD_DOSE"

    def _build_dosing_guidance(
        self, drug_id: str, patient_data: dict, risk: float, gene_recs: dict
    ) -> List[dict]:
        """Build specific dosing guidance items."""
        guidance = []

        # Gene-specific dosing
        for rec in gene_recs.get("dosing_recommendations", []):
            guidance.append({
                "source": f"CPIC Guideline ({rec['gene']})",
                "phenotype": rec["phenotype"],
                "recommendation": rec["recommendation"],
                "priority": "high",
            })

        # Risk-based adjustments
        if risk >= 0.5:
            guidance.append({
                "source": "PharmacoSafe ML Prediction",
                "phenotype": "N/A",
                "recommendation": f"High predicted ADR risk ({risk*100:.0f}%). Consider 50% dose reduction or alternative therapy.",
                "priority": "high",
            })
        elif risk >= 0.3:
            guidance.append({
                "source": "PharmacoSafe ML Prediction",
                "phenotype": "N/A",
                "recommendation": f"Moderate predicted ADR risk ({risk*100:.0f}%). Start at lower dose and titrate carefully.",
                "priority": "medium",
            })

        # Clinical feature adjustments
        age = patient_data.get("age", 50)
        if age >= 75:
            guidance.append({
                "source": "Clinical: Geriatric",
                "phenotype": "N/A",
                "recommendation": "Patient ≥75 years. Consider 25-50% dose reduction. Enhanced monitoring.",
                "priority": "medium",
            })

        egfr = patient_data.get("egfr", 90)
        if egfr < 30:
            guidance.append({
                "source": "Clinical: Renal Impairment",
                "phenotype": "N/A",
                "recommendation": f"Severe renal impairment (eGFR {egfr:.0f}). Dose adjustment required for renally cleared drugs.",
                "priority": "high",
            })
        elif egfr < 60:
            guidance.append({
                "source": "Clinical: Renal Impairment",
                "phenotype": "N/A",
                "recommendation": f"Moderate renal impairment (eGFR {egfr:.0f}). Monitor drug levels.",
                "priority": "medium",
            })

        return guidance

    def _build_monitoring(
        self, drug_id: str, risk: float, patient_data: dict
    ) -> List[str]:
        """Build monitoring recommendations."""
        monitoring = []

        if risk >= 0.3:
            monitoring.append("Increased frequency of clinical assessments")
            monitoring.append("Monitor for early signs of ADR (first 2 weeks critical)")

        drug_info = DRUG_DATABASE.get(drug_id, {})
        adrs = drug_info.get("common_adrs", [])
        if adrs:
            monitoring.append(f"Watch for: {', '.join(adrs[:3])}")

        if drug_id == "warfarin":
            monitoring.append("INR monitoring: baseline, day 3, day 7, then weekly")
        elif drug_id in ("azathioprine", "mercaptopurine"):
            monitoring.append("CBC with differential: weekly for first 8 weeks")
        elif drug_id in ("fluorouracil", "capecitabine"):
            monitoring.append("CBC, liver function: before each cycle")

        n_meds = patient_data.get("n_comedications", 0)
        if n_meds >= 5:
            monitoring.append(f"Polypharmacy alert ({n_meds} co-medications). Review for interactions.")

        return monitoring

    def _suggest_alternatives(self, drug_id: str) -> List[dict]:
        """Suggest alternative drugs when primary is contraindicated."""
        alternatives_map = {
            "warfarin": [
                {"drug": "Rivaroxaban", "reason": "DOAC — no CYP2C9/VKORC1 dependence"},
                {"drug": "Apixaban", "reason": "DOAC — fixed dosing, no INR monitoring"},
            ],
            "clopidogrel": [
                {"drug": "Prasugrel", "reason": "Not dependent on CYP2C19 activation"},
                {"drug": "Ticagrelor", "reason": "Direct P2Y12 inhibitor — no prodrug activation needed"},
            ],
            "codeine": [
                {"drug": "Acetaminophen", "reason": "Non-opioid — no CYP2D6 dependence"},
                {"drug": "Ibuprofen", "reason": "NSAID — different metabolic pathway"},
                {"drug": "Morphine (direct)", "reason": "Active drug — no CYP2D6 activation needed"},
            ],
            "fluorouracil": [
                {"drug": "Oxaliplatin-based regimen", "reason": "Different mechanism — no DPYD dependence"},
            ],
            "azathioprine": [
                {"drug": "Mycophenolate", "reason": "Alternative immunosuppressant — no TPMT dependence"},
            ],
        }

        return alternatives_map.get(drug_id, [
            {"drug": "Consult pharmacist", "reason": "Alternative selection requires clinical review"}
        ])
