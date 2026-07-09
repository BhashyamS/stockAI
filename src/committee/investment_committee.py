import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/executive_agent_recommendations.csv")
OUTPUT_FILE = Path("data/processed/investment_committee_report.csv")


def build_committee_report(row):
    if row["Executive_Action"] == "BUY":
        summary = (
            "The committee recommends buying because the combined agent score is positive "
            "and risk conditions do not block the trade."
        )
    elif row["Executive_Action"] == "SELL":
        summary = (
            "The committee recommends selling or avoiding the position because risk and trend "
            "conditions are unfavorable."
        )
    else:
        summary = (
            "The committee recommends holding because the agents do not show enough agreement "
            "for a strong buy or sell decision."
        )

    return pd.Series({
        "Final_Decision": row["Executive_Action"],
        "Final_Confidence": row["Executive_Confidence"],
        "Position_Size_%": row["Suggested_Position_%"],
        "Committee_Summary": summary,
        "Technical_View": f"{row['Technical_Action']} — {row['Technical_Reason']}",
        "ML_View": f"{row['ML_Action']} — {row['ML_Reason']}",
        "Risk_View": f"{row['Risk_Action']} / {row['Risk_Level']} risk — {row['Risk_Reason']}",
        "Full_Investment_Memo": f"""
INVESTMENT COMMITTEE REPORT

Ticker: {row['Ticker']}
Date: {row['Date']}
Price: ${row['Close']:.2f}

FINAL DECISION: {row['Executive_Action']}
CONFIDENCE: {row['Executive_Confidence']:.0%}
SUGGESTED POSITION SIZE: {row['Suggested_Position_%']}%

TECHNICAL AGENT:
{row['Technical_Action']}
{row['Technical_Reason']}

ML AGENT:
{row['ML_Action']}
5-day up probability: {row['ML_Prob_5D_Up']:.0%}
{row['ML_Reason']}

RISK AGENT:
{row['Risk_Action']} — {row['Risk_Level']} risk
{row['Risk_Reason']}

COMMITTEE SUMMARY:
{summary}

FINAL EXPLANATION:
{row['Executive_Explanation']}
"""
    })


def main():
    df = pd.read_csv(INPUT_FILE)
    latest = df.sort_values("Date").groupby("Ticker").tail(1).copy()

    reports = latest.apply(build_committee_report, axis=1)
    result = pd.concat([latest, reports], axis=1)

    result.to_csv(OUTPUT_FILE, index=False)

    print(result[[
        "Date",
        "Ticker",
        "Final_Decision",
        "Final_Confidence",
        "Position_Size_%",
        "Committee_Summary"
    ]])

    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()