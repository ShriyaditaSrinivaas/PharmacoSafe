"""Run fairness audit across populations for PharmacoSafe."""

import sys
sys.path.insert(0, ".")

import json
import numpy as np
import pandas as pd
from pharmacosafe.config import DATA_DIR, MODELS_DIR, REPORTS_DIR, DRUG_DATABASE
from pharmacosafe.data.preprocessor import DataPreprocessor
from pharmacosafe.models.adr_predictor import ADRPredictor
from pharmacosafe.fairness.auditor import FairnessAuditor
from pharmacosafe.fairness.bias_detector import BiasDetector


def main():
    print("=" * 60)
    print("PharmacoSafe — Fairness Audit")
    print("=" * 60)

    df = pd.read_csv(DATA_DIR / "pharmacogenomic_data.csv")
    preprocessor = DataPreprocessor()
    auditor = FairnessAuditor()
    detector = BiasDetector()

    all_results = {}
    drugs_to_audit = ["warfarin", "clopidogrel", "codeine", "fluorouracil"]

    for drug_id in drugs_to_audit:
        model_path = MODELS_DIR / f"adr_predictor_{drug_id}.joblib"
        if not model_path.exists():
            continue

        model = ADRPredictor.load(drug_id)
        X, y = preprocessor.prepare_features(df, drug_id)
        preds = model.predict(X)
        y_prob = np.array(preds["probabilities"])

        audit = auditor.audit(y.values, y_prob, df["population"].values, drug_id)
        bias = detector.scan(y.values, y_prob, df[["population", "sex", "age_group"]], drug_id)

        all_results[drug_id] = {"fairness_audit": audit, "bias_scan": bias}

        print(f"\n  {drug_id}:")
        print(f"    Demographic Parity: {'✓' if audit['demographic_parity'].get('passed') else '✗'} (disparity: {audit['demographic_parity'].get('disparity', 'N/A')})")
        print(f"    Biases detected: {bias['summary']['n_biases_detected']} (High: {bias['summary']['high']}, Moderate: {bias['summary']['moderate']})")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_DIR / "fairness_audit.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print("\n✓ Fairness audit complete! Results saved to reports/fairness_audit.json")


if __name__ == "__main__":
    main()
