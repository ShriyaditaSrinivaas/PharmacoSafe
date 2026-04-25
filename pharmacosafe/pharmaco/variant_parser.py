"""
Variant Parser for PharmacoSafe.
Parses uploaded patient files (CSV, JSON) and extracts pharmacogenomic data.
"""

import csv
import json
import io
from typing import Dict, Optional

from pharmacosafe.config import PHARMACOGENES


class VariantParser:
    """Parses patient data files and extracts pharmacogenomic profiles."""

    # Column name mappings (handles common variations)
    COLUMN_ALIASES = {
        "age": ["age", "patient_age", "age_years"],
        "sex": ["sex", "gender", "patient_sex"],
        "weight_kg": ["weight_kg", "weight", "body_weight"],
        "height_m": ["height_m", "height", "height_cm"],
        "bmi": ["bmi", "body_mass_index"],
        "egfr": ["egfr", "gfr", "kidney_function", "renal_function"],
        "alt_u_l": ["alt_u_l", "alt", "liver_alt", "sgpt"],
        "n_comedications": ["n_comedications", "comedications", "num_medications", "polypharmacy"],
        "smoking_status": ["smoking_status", "smoking", "smoker"],
        "diabetes": ["diabetes", "diabetic", "t2d"],
        "population": ["population", "ancestry", "ethnicity", "race"],
    }

    # Gene name aliases
    GENE_ALIASES = {
        "CYP2D6": ["CYP2D6", "cyp2d6", "2D6"],
        "CYP2C19": ["CYP2C19", "cyp2c19", "2C19"],
        "CYP2C9": ["CYP2C9", "cyp2c9", "2C9"],
        "CYP3A4": ["CYP3A4", "cyp3a4", "3A4"],
        "DPYD": ["DPYD", "dpyd", "DPD"],
        "TPMT": ["TPMT", "tpmt"],
        "UGT1A1": ["UGT1A1", "ugt1a1"],
        "VKORC1": ["VKORC1", "vkorc1"],
    }

    def parse_csv(self, file_content: str) -> Dict:
        """
        Parse a CSV file containing patient data.

        Expected format: One row per patient with clinical features and gene phenotypes.
        """
        reader = csv.DictReader(io.StringIO(file_content))
        patients = []

        for row in reader:
            patient = self._map_fields(row)
            patients.append(patient)

        return {
            "format": "csv",
            "n_patients": len(patients),
            "patients": patients,
            "validation": self._validate_patients(patients),
        }

    def parse_json(self, file_content: str) -> Dict:
        """Parse a JSON file containing patient data."""
        data = json.loads(file_content)

        # Handle both single patient and array of patients
        if isinstance(data, dict):
            patients = [self._map_fields(data)]
        elif isinstance(data, list):
            patients = [self._map_fields(p) for p in data]
        else:
            raise ValueError("JSON must be an object or array of objects")

        return {
            "format": "json",
            "n_patients": len(patients),
            "patients": patients,
            "validation": self._validate_patients(patients),
        }

    def parse_auto(self, file_content: str, filename: str) -> Dict:
        """Auto-detect format based on file extension and parse."""
        filename_lower = filename.lower()

        if filename_lower.endswith(".csv"):
            return self.parse_csv(file_content)
        elif filename_lower.endswith(".json"):
            return self.parse_json(file_content)
        else:
            # Try JSON first, then CSV
            try:
                return self.parse_json(file_content)
            except (json.JSONDecodeError, ValueError):
                try:
                    return self.parse_csv(file_content)
                except Exception:
                    raise ValueError(
                        f"Could not parse file '{filename}'. "
                        "Supported formats: CSV, JSON"
                    )

    def _map_fields(self, raw: dict) -> dict:
        """Map raw field names to standardized PharmacoSafe fields."""
        patient = {}

        # Map clinical fields
        for standard_name, aliases in self.COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in raw:
                    value = raw[alias]
                    patient[standard_name] = self._coerce_value(standard_name, value)
                    break

        # Map gene phenotypes
        for gene_name, aliases in self.GENE_ALIASES.items():
            phenotype_key = f"{gene_name}_phenotype"

            # Check direct phenotype column
            for alias in aliases:
                for suffix in ["_phenotype", "_status", "_metabolizer", ""]:
                    col_name = f"{alias}{suffix}"
                    if col_name in raw:
                        patient[phenotype_key] = self._normalize_phenotype(
                            raw[col_name], gene_name
                        )
                        break

            # Default to Normal if not found
            if phenotype_key not in patient:
                patient[phenotype_key] = "Normal"

        return patient

    def _normalize_phenotype(self, value: str, gene_name: str) -> str:
        """Normalize phenotype value to standard PharmacoSafe nomenclature."""
        value_lower = str(value).lower().strip()

        gene_info = PHARMACOGENES.get(gene_name, {})
        valid_phenotypes = gene_info.get("phenotypes", [])

        # Direct match (case-insensitive)
        for phenotype in valid_phenotypes:
            if value_lower == phenotype.lower():
                return phenotype

        # Common abbreviation mappings
        abbrev_map = {
            "pm": "Poor",
            "poor metabolizer": "Poor",
            "im": "Intermediate",
            "intermediate metabolizer": "Intermediate",
            "nm": "Normal",
            "em": "Normal",
            "normal metabolizer": "Normal",
            "extensive metabolizer": "Normal",
            "rm": "Rapid",
            "rapid metabolizer": "Rapid",
            "um": "Ultra-rapid",
            "ultra-rapid metabolizer": "Ultra-rapid",
            "ultrarapid": "Ultra-rapid",
            # VKORC1 specific
            "high": "High Sensitivity",
            "sensitive": "High Sensitivity",
            "normal": "Normal Sensitivity" if gene_name == "VKORC1" else "Normal",
            "low": "Low Sensitivity",
            "resistant": "Low Sensitivity",
        }

        normalized = abbrev_map.get(value_lower)
        if normalized and normalized in valid_phenotypes:
            return normalized

        # Default
        return valid_phenotypes[len(valid_phenotypes) // 2] if valid_phenotypes else "Normal"

    def _coerce_value(self, field_name: str, value) -> object:
        """Coerce a value to the expected type for a field."""
        try:
            if field_name in ("age", "n_comedications", "diabetes"):
                return int(float(value))
            elif field_name in ("weight_kg", "height_m", "bmi", "egfr", "alt_u_l"):
                return float(value)
            else:
                return str(value)
        except (ValueError, TypeError):
            return value

    def _validate_patients(self, patients: list) -> dict:
        """Validate parsed patient data."""
        issues = []
        warnings = []

        for i, patient in enumerate(patients):
            pid = f"Patient {i + 1}"

            # Check age
            age = patient.get("age")
            if age is not None:
                if not (0 < age < 120):
                    issues.append(f"{pid}: Invalid age ({age})")
            else:
                warnings.append(f"{pid}: Missing age")

            # Check weight
            weight = patient.get("weight_kg")
            if weight is not None and not (20 < weight < 300):
                issues.append(f"{pid}: Invalid weight ({weight} kg)")

            # Check eGFR
            egfr = patient.get("egfr")
            if egfr is not None and not (0 < egfr < 200):
                warnings.append(f"{pid}: eGFR value outside expected range ({egfr})")

        return {
            "valid": len(issues) == 0,
            "n_issues": len(issues),
            "n_warnings": len(warnings),
            "issues": issues,
            "warnings": warnings,
        }
