import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/features.csv")
OUTPUT_FILE = Path("data/processed/features_clean.csv")


def clean_features():
    df = pd.read_csv(INPUT_FILE)

    print("Before cleaning:")
    print(df.shape)
    print(df.isnull().sum())

    df = df.dropna()

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nAfter cleaning:")
    print(df.shape)
    print(df.isnull().sum())

    print(f"\nSaved clean features to {OUTPUT_FILE}")


if __name__ == "__main__":
    clean_features()