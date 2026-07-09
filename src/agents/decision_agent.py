import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/ml_predictions.csv")
OUTPUT_FILE = Path("data/processed/agent_recommendations.csv")


def calculate_position_size(action, confidence, atr_ratio):
    if action != "BUY":
        return 0.0

    base_size = confidence * 5  # max 5% position

    if atr_ratio > 0.06:
        base_size *= 0.5
    elif atr_ratio < 0.03:
        base_size *= 1.2

    return round(min(base_size, 5), 2)


def make_recommendation(row):
    score = 0
    reasons = []

    if row["ML_Prob_5D_Up"] >= 0.60:
        score += 2
        reasons.append("ML model is bullish")
    elif row["ML_Prob_5D_Up"] <= 0.45:
        score -= 2
        reasons.append("ML model is bearish")

    if row["Close"] > row["MA_200"]:
        score += 1
        reasons.append("price is above the 200-day trend")
    else:
        score -= 1
        reasons.append("price is below the 200-day trend")

    if row["MA_50"] > row["MA_200"]:
        score += 1
        reasons.append("medium-term trend is positive")

    if row["Momentum_10"] > 0:
        score += 1
        reasons.append("recent momentum is positive")
    else:
        score -= 1
        reasons.append("recent momentum is negative")

    if row["RSI_14"] > 75:
        score -= 1
        reasons.append("RSI is overbought")

    if row["ATR_Ratio"] > 0.08:
        score -= 1
        reasons.append("volatility is high")

    if score >= 3:
        action = "BUY"
    elif score <= -2:
        action = "SELL"
    else:
        action = "HOLD"

    confidence = round(min(abs(score) / 6, 1), 2)
    position_size = calculate_position_size(action, confidence, row["ATR_Ratio"])

    explanation = (
        f"{action} with {confidence:.0%} confidence. "
        f"Suggested position size: {position_size}% of portfolio. "
        f"Reasoning: " + "; ".join(reasons) + "."
    )

    return pd.Series({
        "Agent_Action": action,
        "Agent_Confidence": confidence,
        "Suggested_Position_%": position_size,
        "Agent_Explanation": explanation
    })


def main():
    df = pd.read_csv(INPUT_FILE)

    recommendations = df.apply(make_recommendation, axis=1)
    result = pd.concat([df, recommendations], axis=1)

    latest = result.sort_values("Date").groupby("Ticker").tail(1)

    result.to_csv(OUTPUT_FILE, index=False)

    print(latest[[
        "Date",
        "Ticker",
        "Close",
        "ML_Prob_5D_Up",
        "Agent_Action",
        "Agent_Confidence",
        "Suggested_Position_%",
        "Agent_Explanation"
    ]])

    print(f"\nSaved recommendations to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()