from pathlib import Path
import pandas as pd

FEATURES_FILE = Path("data/processed/features_clean.csv")
ML_FILE = Path("data/processed/ml_predictions.csv")
OUTPUT_FILE = Path("data/processed/market_screener_results.csv")


def normalize(value, low, high):
    if high == low:
        return 0
    return max(0, min((value - low) / (high - low), 1))


def screen_stock(row):
    score = 0
    reasons = []

    if row["Close"] > row["MA_200"]:
        score += 20
        reasons.append("price above MA200")

    if row["MA_50"] > row["MA_200"]:
        score += 15
        reasons.append("MA50 above MA200")

    if row["Momentum_10"] > 0:
        score += 15
        reasons.append("positive 10-day momentum")

    if 35 <= row["RSI_14"] <= 65:
        score += 10
        reasons.append("RSI in healthy range")
    elif row["RSI_14"] < 35:
        score += 5
        reasons.append("RSI may be oversold")

    if row["ATR_Ratio"] < 0.04:
        score += 10
        reasons.append("low volatility")

    if row["ML_Prob_5D_Up"] > 0.55:
        score += 20
        reasons.append("ML model leans bullish")
    elif row["ML_Prob_5D_Up"] > 0.50:
        score += 10
        reasons.append("ML model slightly bullish")

    if row["Drop_From_20D_High"] > -0.05:
        score += 10
        reasons.append("near recent highs")

    return pd.Series({
        "Screening_Score": round(score, 2),
        "Screening_Reason": "; ".join(reasons) if reasons else "No strong screening signals",
    })


def main():
    features = pd.read_csv(FEATURES_FILE)
    ml = pd.read_csv(ML_FILE)

    latest_features = features.sort_values("Date").groupby("Ticker").tail(1)
    latest_ml = ml.sort_values("Date").groupby("Ticker").tail(1)[
        ["Ticker", "ML_Prob_5D_Up", "ML_Signal"]
    ]

    df = latest_features.merge(latest_ml, on="Ticker", how="left")

    scores = df.apply(screen_stock, axis=1)
    result = pd.concat([df, scores], axis=1)

    result = result.sort_values("Screening_Score", ascending=False)

    result[
        [
            "Date",
            "Ticker",
            "Close",
            "Screening_Score",
            "ML_Prob_5D_Up",
            "RSI_14",
            "Momentum_10",
            "ATR_Ratio",
            "Screening_Reason",
        ]
    ].to_csv(OUTPUT_FILE, index=False)

    print(result[
        [
            "Ticker",
            "Close",
            "Screening_Score",
            "ML_Prob_5D_Up",
            "Screening_Reason",
        ]
    ])

    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()