from pathlib import Path
import pandas as pd

FEATURES_FILE = Path("data/processed/features_clean.csv")
SCREENER_FILE = Path("data/processed/market_screener_results.csv")
OUTPUT_FILE = Path("data/processed/fundamental_agent_results.csv")


def analyze(row):
    score = 50
    positives = []
    negatives = []
    risks = []

    if row["Close"] > row["MA_200"]:
        score += 15
        positives.append("Long-term price trend is positive")
    else:
        score -= 15
        negatives.append("Price is below long-term trend")

    if row["Momentum_10"] > 0:
        score += 10
        positives.append("Recent momentum is positive")
    else:
        score -= 5
        negatives.append("Recent momentum is weak")

    if row["ATR_Ratio"] < 0.04:
        score += 10
        positives.append("Volatility is controlled")
    elif row["ATR_Ratio"] > 0.08:
        score -= 15
        risks.append("Volatility is elevated")

    if row["Drop_From_20D_High"] < -0.15:
        score -= 10
        risks.append("Large recent pullback from 20-day high")

    score = max(0, min(score, 100))

    if score >= 70:
        view = "STRONG"
    elif score >= 50:
        view = "NEUTRAL"
    else:
        view = "WEAK"

    return pd.Series({
        "Fundamental_View": view,
        "Fundamental_Score": round(score, 2),
        "Fundamental_Positives": "; ".join(positives),
        "Fundamental_Negatives": "; ".join(negatives),
        "Fundamental_Risks": "; ".join(risks),
    })


def main():
    features = pd.read_csv(FEATURES_FILE)
    latest = features.sort_values("Date").groupby("Ticker").tail(1)

    output = latest.apply(analyze, axis=1)
    result = pd.concat([latest[["Date", "Ticker", "Close"]], output], axis=1)

    result.to_csv(OUTPUT_FILE, index=False)

    print(result)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()