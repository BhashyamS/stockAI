import json
from pathlib import Path

import pandas as pd

from src.agents.technical.opinion import TechnicalOpinionAgent
from src.agents.ml.opinion import MLOpinionAgent
from src.agents.risk.opinion import RiskOpinionAgent
from src.committee.orchestrator import InvestmentCommitteeOrchestrator

INPUT_FILE = Path("data/processed/ml_predictions.csv")
OUTPUT_JSON = Path("data/processed/structured_committee_results.json")
OUTPUT_CSV = Path("data/processed/structured_committee_summary.csv")


def main():
    df = pd.read_csv(INPUT_FILE)
    latest = df.sort_values("Date").groupby("Ticker").tail(1)

    agents = [
        TechnicalOpinionAgent(),
        MLOpinionAgent(),
        RiskOpinionAgent(),
    ]

    committee = InvestmentCommitteeOrchestrator(agents)

    results = []
    summaries = []

    for _, row in latest.iterrows():
        result = committee.run_committee(row)
        results.append(result)

        summaries.append({
            "Date": row["Date"],
            "Ticker": result["ticker"],
            "Final_Action": result["weighted_vote"]["final_action"],
            "Committee_Score": result["weighted_vote"]["committee_score"],
            "Buy_Votes": result["vote_summary"]["buy_votes"],
            "Hold_Votes": result["vote_summary"]["hold_votes"],
            "Sell_Votes": result["vote_summary"]["sell_votes"],
            "Avg_Confidence": result["vote_summary"]["avg_confidence"],
            "Has_Disagreement": result["debate"]["has_disagreement"],
            "Debate_Summary": result["debate"]["summary"],
        })

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    pd.DataFrame(summaries).to_csv(OUTPUT_CSV, index=False)

    print(pd.DataFrame(summaries))
    print(f"\nSaved JSON to {OUTPUT_JSON}")
    print(f"Saved CSV to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()