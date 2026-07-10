import json
from pathlib import Path

import pandas as pd

SUMMARY_FILE = Path("data/processed/structured_committee_summary.csv")
FEATURES_FILE = Path("data/processed/features_clean.csv")
OUTPUT_FILE = Path("data/processed/portfolio_allocation_plan.csv")


def position_size(row, cash):
    action = row["Final_Action"]
    score = row["Committee_Score"]
    confidence = row["Avg_Confidence"]
    disagreement = row["Has_Disagreement"]

    if action != "BUY":
        return 0.0

    base_pct = 0.03

    if score > 0.50:
        base_pct += 0.03
    elif score > 0.25:
        base_pct += 0.02

    if confidence > 0.60:
        base_pct += 0.02
    elif confidence < 0.25:
        base_pct -= 0.01

    if disagreement:
        base_pct -= 0.01

    final_pct = max(0.0, min(base_pct, 0.08))
    return round(cash * final_pct, 2)


def main():
    cash = float(input("Enter available paper trading cash: "))

    summary = pd.read_csv(SUMMARY_FILE)
    features = pd.read_csv(FEATURES_FILE)

    latest_features = features.sort_values("Date").groupby("Ticker").tail(1)

    df = summary.merge(
        latest_features[["Ticker", "Close", "RSI_14", "ATR_Ratio", "Momentum_10"]],
        on="Ticker",
        how="left",
    )

    plans = []

    for _, row in df.iterrows():
        dollar_amount = position_size(row, cash)
        shares = dollar_amount / row["Close"] if row["Close"] > 0 else 0

        if row["Final_Action"] == "BUY" and dollar_amount > 0:
            recommendation = "BUY"
            reason = "Positive committee signal with acceptable risk and confidence."
        elif row["Final_Action"] == "SELL":
            recommendation = "AVOID"
            reason = "Committee signal is bearish."
        else:
            recommendation = "WATCH"
            reason = "Committee does not show enough conviction to buy."

        plans.append({
            "Ticker": row["Ticker"],
            "Recommendation": recommendation,
            "Committee_Action": row["Final_Action"],
            "Committee_Score": row["Committee_Score"],
            "Avg_Confidence": row["Avg_Confidence"],
            "Has_Disagreement": row["Has_Disagreement"],
            "Current_Price": row["Close"],
            "Dollar_Amount": dollar_amount,
            "Estimated_Shares": round(shares, 4),
            "Reason": reason,
        })

    out = pd.DataFrame(plans)
    out = out.sort_values(["Recommendation", "Dollar_Amount"], ascending=[True, False])
    out.to_csv(OUTPUT_FILE, index=False)

    print(out)
    print(f"\nSaved portfolio allocation plan to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()