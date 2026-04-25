"""
Clinical Report Generator for PharmacoSafe.
Generates structured clinical reports with risk assessments and recommendations.
"""

import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from pharmacosafe.config import REPORTS_DIR, DRUG_DATABASE


class ClinicalReportGenerator:
    """Generates structured clinical reports combining predictions, explanations, and recommendations."""

    def generate(self, patient_data: dict, drug_id: str, prediction: dict,
                 shap_explanation: dict, dosing_rec: dict) -> dict:
        """Generate a complete clinical report."""
        drug_info = DRUG_DATABASE.get(drug_id, {})

        report = {
            "report_id": f"PSR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "disclaimer": "RESEARCH USE ONLY. Not for clinical decision-making.",
            "patient_summary": {
                "age": patient_data.get("age"),
                "sex": patient_data.get("sex"),
                "population": patient_data.get("population"),
                "weight_kg": patient_data.get("weight_kg"),
                "egfr": patient_data.get("egfr"),
                "n_comedications": patient_data.get("n_comedications"),
            },
            "drug": {
                "name": drug_info.get("name", drug_id),
                "class": drug_info.get("class", "Unknown"),
                "indication": drug_info.get("indication", ""),
            },
            "risk_assessment": {
                "adr_probability": prediction.get("probability", 0),
                "risk_percent": prediction.get("risk_percent", 0),
                "risk_level": prediction.get("risk_level", "Unknown"),
            },
            "key_risk_factors": shap_explanation.get("top_risk_factors", [])[:5],
            "protective_factors": shap_explanation.get("top_protective_factors", [])[:3],
            "dosing_recommendation": {
                "action": dosing_rec.get("action", ""),
                "guidance": dosing_rec.get("dosing_guidance", []),
                "monitoring": dosing_rec.get("monitoring", []),
                "warnings": dosing_rec.get("warnings", []),
                "alternatives": dosing_rec.get("alternatives", []),
            },
            "gene_interactions": dosing_rec.get("gene_interactions", []),
        }
        return report

    def save(self, report: dict, filename: Optional[str] = None) -> Path:
        """Save report to JSON file."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        if filename is None:
            filename = f"{report['report_id']}.json"
        filepath = REPORTS_DIR / filename
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
        return filepath
