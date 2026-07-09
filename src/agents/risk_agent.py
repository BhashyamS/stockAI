import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/features_clean.csv")
OUTPUT_FILE = Path("data/processed/risk_agent_signals.csv")


def analyze_risk(row):
    risk_score = 0
    reasons = []

    if row["ATR_Ratio"] > 0.08:
        risk_score += 2
        reasons.append("ATR volatility is high")
    elif row["ATR_Ratio"] > 0.05:
        risk_score += 1
        reasons.append("ATR volatility is moderate")
    else:
        reasons.append("ATR volatility is low")

    if row["Close"] < row["MA_200"]:
        risk_score += 2
        reasons.append("price is below the 200-day moving average")

    if row["Drop_From_20D_High"] < -0.10:
        risk_score += 1
        reasons.append("stock is down more than 10% from its 20-day high")

    if row["Momentum_10"] < -0.05:
        risk_score += 1
        reasons.append("10-day momentum is sharply negative")

    if risk_score >= 4:
        action = "SELL"
        risk_level = "HIGH"
    elif risk_score >= 2:
        action = "HOLD"
        risk_level = "MEDIUM"
    else:
        action = "BUY"
        risk_level = "LOW"

    confidence = round(min(risk_score / 5, 1), 2)

    return pd.Series({
        "Risk_Action": action,
        "Risk_Level": risk_level,
        "Risk_Confidence": confidence,
        "Risk_Score": risk_score,
        "Risk_Reason": "; ".join(reasons)
    })


def main():
    df = pd.read_csv(INPUT_FILE)

    output = df.apply(analyze_risk, axis=1)
    result = pd.concat([df, output], axis=1)

    result.to_csv(OUTPUT_FILE, index=False)

    latest = result.sort_values("Date").groupby("Ticker").tail(1)

    print(latest[[
        "Date",
        "Ticker",
        "Close",
        "ATR_Ratio",
        "Risk_Action",
        "Risk_Level",
        "Risk_Score",
        "Risk_Reason"
    ]])

    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()