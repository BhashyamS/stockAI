import pandas as pd
import joblib
from pathlib import Path

INPUT_FILE = Path("data/processed/features_clean.csv")
MODEL_FILE = Path("models/random_forest_5d_model.pkl")
OUTPUT_FILE = Path("data/processed/ml_predictions.csv")

FEATURES = [
    "Daily_Return",
    "MA_5",
    "MA_20",
    "MA_50",
    "MA_200",
    "Volatility_20",
    "Momentum_10",
    "Volume_Ratio",
    "RSI_14",
    "ATR_Ratio",
]


def main():
    df = pd.read_csv(INPUT_FILE)
    model = joblib.load(MODEL_FILE)

    df["ML_Prob_5D_Up"] = model.predict_proba(df[FEATURES])[:, 1]

    df["ML_Signal"] = "HOLD"
    df.loc[df["ML_Prob_5D_Up"] >= 0.60, "ML_Signal"] = "BUY"
    df.loc[df["ML_Prob_5D_Up"] <= 0.45, "ML_Signal"] = "SELL"

    df.to_csv(OUTPUT_FILE, index=False)

    print(df[["Date", "Ticker", "Close", "ML_Prob_5D_Up", "ML_Signal"]].tail(20))
    print(f"\nSaved predictions to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()