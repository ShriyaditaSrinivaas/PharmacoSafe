"""Train all ADR prediction models for PharmacoSafe."""

import sys
sys.path.insert(0, ".")

import pandas as pd
from pharmacosafe.config import DATA_DIR, ModelConfig
from pharmacosafe.models.trainer import TrainingPipeline


def main():
    print("=" * 60)
    print("PharmacoSafe — Model Training Pipeline")
    print("=" * 60)

    data_path = DATA_DIR / "pharmacogenomic_data.csv"
    if not data_path.exists():
        print("ERROR: Data not found. Run 'python scripts/generate_data.py' first.")
        return

    df = pd.read_csv(data_path)
    print(f"\nLoaded {len(df)} samples with {len(df.columns)} features")

    # Train on a subset of drugs for speed
    priority_drugs = [
        "warfarin", "clopidogrel", "codeine", "fluorouracil",
        "azathioprine", "irinotecan", "simvastatin", "tamoxifen",
    ]

    pipeline = TrainingPipeline(ModelConfig())
    print(f"\nTraining models for {len(priority_drugs)} drugs...")

    results = pipeline.run(df, drugs=priority_drugs)

    print(f"\n{'Drug':<20} {'CV AUC':>10} {'Test AUC':>10} {'Brier':>10}")
    print("-" * 55)
    for drug_id in priority_drugs:
        train = results["train_metrics"].get(drug_id, {})
        test = results["test_metrics"].get(drug_id, {})
        cv_auc = train.get("cv_auc_mean", 0)
        test_auc = test.get("auc_roc", 0)
        brier = test.get("brier_score", 0)
        print(f"  {drug_id:<18} {cv_auc:>10.3f} {test_auc:>10.3f} {brier:>10.3f}")

    if results.get("ensemble_metrics"):
        print(f"\n  Ensemble Train AUC: {results['ensemble_metrics'].get('ensemble_train_auc', 0):.3f}")

    pipeline.save_results()
    print("\n✓ All models trained and saved!")


if __name__ == "__main__":
    main()
