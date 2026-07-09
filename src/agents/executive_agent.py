import pandas as pd
from pathlib import Path

TECH_FILE = Path("data/processed/technical_agent_signals.csv")
ML_FILE = Path("data/processed/ml_agent_signals.csv")
RISK_FILE = Path("data/processed/risk_agent_signals.csv")
OUTPUT_FILE = Path("data/processed/executive_agent_recommendations.csv")


ACTION_SCORE = {
    "BUY": 1,
    "HOLD": 0,
    "SELL": -1
}


def final_decision(row):
    technical_vote = ACTION_SCORE[row["Technical_Action"]] * row["Technical_Confidence"]
    ml_vote = ACTION_SCORE[row["ML_Action"]] * row["ML_Confidence"]
    risk_vote = ACTION_SCORE[row["Risk_Action"]] * row["Risk_Confidence"]

    final_score = technical_vote + ml_vote + risk_vote

    if row["Risk_Level"] == "HIGH":
        action = "SELL"
    elif final_score >= 0.6:
        action = "BUY"
    elif final_score <= -0.6:
        action = "SELL"
    else:
        action = "HOLD"

    confidence = round(min(abs(final_score) / 2, 1), 2)

    if action == "BUY":
        position_size = round(confidence * 5, 2)
    else:
        position_size = 0.0

    explanation = (
        f"Final decision is {action}. "
        f"Technical Agent says {row['Technical_Action']} because {row['Technical_Reason']}. "
        f"ML Agent says {row['ML_Action']} because {row['ML_Reason']}. "
        f"Risk Agent says {row['Risk_Action']} with {row['Risk_Level']} risk because {row['Risk_Reason']}. "
        f"Suggested position size is {position_size}%."
    )

    return pd.Series({
        "Executive_Action": action,
        "Executive_Confidence": confidence,
        "Suggested_Position_%": position_size,
        "Executive_Score": round(final_score, 2),
        "Executive_Explanation": explanation
    })


def main():
    tech = pd.read_csv(TECH_FILE)
    ml = pd.read_csv(ML_FILE)
    risk = pd.read_csv(RISK_FILE)

    keep_tech = [
        "Date", "Ticker", "Close",
        "Technical_Action", "Technical_Confidence",
        "Technical_Score", "Technical_Reason"
    ]

    keep_ml = [
        "Date", "Ticker",
        "ML_Prob_5D_Up", "ML_Action",
        "ML_Confidence", "ML_Reason"
    ]

    keep_risk = [
        "Date", "Ticker",
        "Risk_Action", "Risk_Level",
        "Risk_Confidence", "Risk_Score", "Risk_Reason"
    ]

    df = tech[keep_tech].merge(
        ml[keep_ml],
        on=["Date", "Ticker"],
        how="inner"
    ).merge(
        risk[keep_risk],
        on=["Date", "Ticker"],
        how="inner"
    )

    output = df.apply(final_decision, axis=1)
    result = pd.concat([df, output], axis=1)

    result.to_csv(OUTPUT_FILE, index=False)

    latest = result.sort_values("Date").groupby("Ticker").tail(1)

    print(latest[[
        "Date",
        "Ticker",
        "Close",
        "Technical_Action",
        "ML_Action",
        "Risk_Action",
        "Risk_Level",
        "Executive_Action",
        "Executive_Confidence",
        "Suggested_Position_%"
    ]])

    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()