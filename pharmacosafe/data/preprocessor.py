"""
Data preprocessor for PharmacoSafe.
Handles validation, cleaning, feature encoding, and train/test splitting.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Tuple, Dict, Optional

from pharmacosafe.config import PHARMACOGENES, POPULATIONS, ModelConfig


class DataPreprocessor:
    """Validates, cleans, and encodes pharmacogenomic data for model training."""

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler = StandardScaler()
        self._fitted = False

    def validate(self, df: pd.DataFrame) -> dict:
        """Validate the dataset structure and contents."""
        issues = []
        warnings = []

        # Check required columns
        required_cols = ["patient_id", "population", "age", "sex", "weight_kg"]
        for col in required_cols:
            if col not in df.columns:
                issues.append(f"Missing required column: {col}")

        # Check pharmacogene columns
        for gene in PHARMACOGENES:
            col = f"{gene}_phenotype"
            if col not in df.columns:
                warnings.append(f"Missing pharmacogene column: {col}")

        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            cols_with_missing = missing[missing > 0].to_dict()
            warnings.append(f"Columns with missing values: {cols_with_missing}")

        # Check population values
        if "population" in df.columns:
            unknown_pops = set(df["population"].unique()) - set(POPULATIONS)
            if unknown_pops:
                warnings.append(f"Unknown populations: {unknown_pops}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "n_samples": len(df),
            "n_features": len(df.columns),
        }

    def prepare_features(
        self, df: pd.DataFrame, target_drug: str
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare feature matrix X and target vector y for a specific drug.

        Args:
            df: Raw dataset
            target_drug: Drug ID (e.g., 'warfarin')

        Returns:
            X: Feature DataFrame (encoded)
            y: Binary ADR outcome
        """
        target_col = f"adr_{target_drug}"
        if target_col not in df.columns:
            raise ValueError(f"No ADR outcome column for drug: {target_drug}")

        # Select feature columns
        feature_cols = self._get_feature_columns(df, target_drug)
        X = df[feature_cols].copy()
        y = df[target_col].copy()

        # Encode categorical variables
        categorical_cols = X.select_dtypes(include=["object", "category"]).columns
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col].astype(str))
            else:
                # Handle unseen categories
                known = set(self.label_encoders[col].classes_)
                X[col] = X[col].astype(str).apply(
                    lambda v: v if v in known else self.label_encoders[col].classes_[0]
                )
                X[col] = self.label_encoders[col].transform(X[col])

        # Fill remaining NAs
        X = X.fillna(0)

        return X, y

    def split(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        populations: pd.Series,
    ) -> dict:
        """Stratified train/test split preserving population distribution."""
        # Create stratification key
        strat_key = populations.astype(str) + "_" + y.astype(str)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.config.test_size,
            stratify=strat_key,
            random_state=self.config.random_state,
        )

        pop_train = populations.loc[X_train.index]
        pop_test = populations.loc[X_test.index]

        return {
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
            "pop_train": pop_train,
            "pop_test": pop_test,
        }

    def prepare_single_patient(self, patient_data: dict, drug_id: str) -> pd.DataFrame:
        """
        Prepare features for a single patient input (from the UI).

        Args:
            patient_data: Dict with patient clinical + genetic data
            drug_id: Target drug

        Returns:
            Feature DataFrame (1 row, encoded)
        """
        # Build a single-row DataFrame
        row = {}

        # Clinical features
        row["age"] = patient_data.get("age", 50)
        row["sex"] = patient_data.get("sex", "Male")
        row["weight_kg"] = patient_data.get("weight_kg", 70)
        row["bmi"] = patient_data.get("bmi", 24.0)
        row["egfr"] = patient_data.get("egfr", 90)
        row["alt_u_l"] = patient_data.get("alt_u_l", 25)
        row["n_comedications"] = patient_data.get("n_comedications", 2)
        row["smoking_status"] = patient_data.get("smoking_status", "Never")
        row["diabetes"] = patient_data.get("diabetes", 0)
        row["population"] = patient_data.get("population", "EUR")

        # Age group
        age = row["age"]
        if age <= 30:
            row["age_group"] = "Young"
        elif age <= 50:
            row["age_group"] = "Middle"
        elif age <= 65:
            row["age_group"] = "Senior"
        else:
            row["age_group"] = "Elderly"

        # Pharmacogene phenotypes
        for gene in PHARMACOGENES:
            col = f"{gene}_phenotype"
            row[col] = patient_data.get(col, "Normal")

        df = pd.DataFrame([row])

        # Get feature columns (without target-specific risk columns)
        feature_cols = [c for c in self._get_base_feature_columns() if c in df.columns]
        X = df[feature_cols].copy()

        # Encode
        categorical_cols = X.select_dtypes(include=["object", "category"]).columns
        for col in categorical_cols:
            if col in self.label_encoders:
                known = set(self.label_encoders[col].classes_)
                X[col] = X[col].astype(str).apply(
                    lambda v: v if v in known else self.label_encoders[col].classes_[0]
                )
                X[col] = self.label_encoders[col].transform(X[col])
            else:
                # Fallback: encode as 0
                X[col] = 0

        X = X.fillna(0)
        return X

    def _get_feature_columns(self, df: pd.DataFrame, target_drug: str) -> list:
        """Get feature columns for a specific drug target."""
        exclude_prefixes = ["patient_id", "adr_", "adr_risk_"]
        cols = []
        for col in df.columns:
            if any(col.startswith(p) for p in exclude_prefixes):
                continue
            cols.append(col)
        return cols

    def _get_base_feature_columns(self) -> list:
        """Get base feature columns (without target-specific ones)."""
        cols = [
            "age", "sex", "weight_kg", "bmi", "egfr", "alt_u_l",
            "n_comedications", "smoking_status", "diabetes",
            "population", "age_group",
        ]
        for gene in PHARMACOGENES:
            cols.append(f"{gene}_phenotype")
        return cols
