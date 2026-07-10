from pathlib import Path

import pandas as pd

SUMMARY_FILE = Path("data/processed/structured_committee_summary.csv")
FEATURES_FILE = Path("data/processed/features_clean.csv")
OUTPUT_FILE = Path("data/processed/portfolio_allocation_plan.csv")


def normalize(value, low, high):
    if high == low:
        return 0
    return max(0, min((value - low) / (high - low), 1))


def opportunity_score(row):
    score = 0

    # Committee score matters most
    score += normalize(row["Committee_Score"], -0.5, 0.5) * 40

    # Confidence matters
    score += row["Avg_Confidence"] * 20

    # Positive momentum helps
    score += normalize(row["Momentum_10"], -0.10, 0.10) * 15

    # RSI recovery zone helps
    if 30 <= row["RSI_14"] <= 60:
        score += 10
    elif row["RSI_14"] < 30:
        score += 5
    elif row["RSI_14"] > 75:
        score -= 10

    # Lower volatility helps
    if row["ATR_Ratio"] < 0.04:
        score += 10
    elif row["ATR_Ratio"] > 0.08:
        score -= 15

    # Disagreement penalty
    if row["Has_Disagreement"]:
        score -= 7

    # Bearish final action penalty
    if row["Final_Action"] == "SELL":
        score -= 25

    return round(max(0, min(score, 100)), 2)


def recommendation_from_score(score):
    if score >= 65:
        return "BUY"
    elif score >= 45:
        return "SMALL BUY"
    elif score >= 30:
        return "WATCH"
    return "AVOID"


def allocation_percent(score, recommendation):
    if recommendation == "BUY":
        return min(0.08, score / 1000)
    if recommendation == "SMALL BUY":
        return min(0.03, score / 1500)
    return 0.0


def build_reason(row, score, recommendation):
    reasons = []

    reasons.append(f"Opportunity score is {score}/100")

    if row["Committee_Score"] > 0:
        reasons.append("committee score is positive")
    elif row["Committee_Score"] < 0:
        reasons.append("committee score is negative")
    else:
        reasons.append("committee score is neutral")

    if row["Momentum_10"] > 0:
        reasons.append("momentum is positive")
    else:
        reasons.append("momentum is weak")

    if row["ATR_Ratio"] < 0.04:
        reasons.append("volatility is relatively low")
    elif row["ATR_Ratio"] > 0.08:
        reasons.append("volatility is elevated")

    if row["Has_Disagreement"]:
        reasons.append("agents disagree, so sizing is reduced")

    if recommendation in ["BUY", "SMALL BUY"]:
        reasons.append("allocation is intentionally small because this is a paper-trading research system")

    return "; ".join(reasons)


def main():
    cash = float(input("Enter available paper trading cash: "))

    summary = pd.read_csv(SUMMARY_FILE)
    features = pd.read_csv(FEATURES_FILE)

    latest_features = features.sort_values("Date").groupby("Ticker").tail(1)

    df = summary.merge(
        latest_features[
            [
                "Ticker",
                "Close",
                "RSI_14",
                "ATR_Ratio",
                "Momentum_10",
                "Drop_From_20D_High",
            ]
        ],
        on="Ticker",
        how="left",
    )

    plans = []

    for _, row in df.iterrows():
        score = opportunity_score(row)
        recommendation = recommendation_from_score(score)
        alloc_pct = allocation_percent(score, recommendation)
        dollar_amount = round(cash * alloc_pct, 2)
        shares = dollar_amount / row["Close"] if row["Close"] > 0 else 0

        plans.append({
            "Ticker": row["Ticker"],
            "Recommendation": recommendation,
            "Opportunity_Score": score,
            "Allocation_%": round(alloc_pct * 100, 2),
            "Dollar_Amount": dollar_amount,
            "Estimated_Shares": round(shares, 4),
            "Committee_Action": row["Final_Action"],
            "Committee_Score": row["Committee_Score"],
            "Avg_Confidence": row["Avg_Confidence"],
            "Has_Disagreement": row["Has_Disagreement"],
            "Current_Price": row["Close"],
            "RSI_14": row["RSI_14"],
            "Momentum_10": row["Momentum_10"],
            "ATR_Ratio": row["ATR_Ratio"],
            "Reason": build_reason(row, score, recommendation),
        })

    out = pd.DataFrame(plans)
    out = out.sort_values("Opportunity_Score", ascending=False)
    out.to_csv(OUTPUT_FILE, index=False)

    print(out)
    print(f"\nSaved portfolio allocation plan to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()