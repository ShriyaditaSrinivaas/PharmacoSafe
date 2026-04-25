"""Generate synthetic pharmacogenomic data for PharmacoSafe."""

import sys
sys.path.insert(0, ".")

from pharmacosafe.data.generator import PharmacogenomicDataGenerator
from pharmacosafe.config import DataConfig


def main():
    print("=" * 60)
    print("PharmacoSafe — Synthetic Data Generation")
    print("=" * 60)

    config = DataConfig(n_samples=3000)
    generator = PharmacogenomicDataGenerator(config)

    print(f"\nGenerating {config.n_samples} synthetic patients...")
    df = generator.generate()

    filepath = generator.save(df)
    print(f"✓ Dataset saved to: {filepath}")
    print(f"  Samples: {len(df)}")
    print(f"  Features: {len(df.columns)}")
    print(f"\n  Population distribution:")
    for pop, count in df["population"].value_counts().items():
        print(f"    {pop}: {count} ({count/len(df)*100:.1f}%)")

    # ADR prevalence
    adr_cols = [c for c in df.columns if c.startswith("adr_") and not c.startswith("adr_risk_")]
    print(f"\n  ADR prevalence (top 5):")
    for col in sorted(adr_cols, key=lambda c: df[c].mean(), reverse=True)[:5]:
        drug = col.replace("adr_", "")
        print(f"    {drug}: {df[col].mean()*100:.1f}%")

    print("\n✓ Data generation complete!")


if __name__ == "__main__":
    main()
