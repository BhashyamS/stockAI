import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/ml_predictions.csv")
OUTPUT_FILE = Path("data/processed/ml_agent_signals.csv")


def analyze_ml(row):
    prob = row["ML_Prob_5D_Up"]

    if prob >= 0.60:
        action = "BUY"
        reason = "ML model predicts a strong probability of positive 5-day return"
    elif prob <= 0.45:
        action = "SELL"
        reason = "ML model predicts weak probability of positive 5-day return"
    else:
        action = "HOLD"
        reason = "ML model does not show a strong edge"

    confidence = round(abs(prob - 0.50) * 2, 2)

    return pd.Series({
        "ML_Action": action,
        "ML_Confidence": confidence,
        "ML_Reason": reason
    })


def main():
    df = pd.read_csv(INPUT_FILE)

    output = df.apply(analyze_ml, axis=1)
    result = pd.concat([df, output], axis=1)

    result.to_csv(OUTPUT_FILE, index=False)

    latest = result.sort_values("Date").groupby("Ticker").tail(1)

    print(latest[[
        "Date",
        "Ticker",
        "Close",
        "ML_Prob_5D_Up",
        "ML_Action",
        "ML_Confidence",
        "ML_Reason"
    ]])

    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()