import json
from pathlib import Path

import pandas as pd

MEMORY_FILE = Path("data/committee_memory.json")
OUTPUT_FILE = Path("data/processed/committee_memory_summary.csv")


def main():
    if not MEMORY_FILE.exists():
        print("No committee memory found yet.")
        return

    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)

    rows = []

    for item in memory:
        result = item["committee_result"]

        rows.append({
            "Timestamp": item["timestamp"],
            "Ticker": item["ticker"],
            "Final_Action": result["weighted_vote"]["final_action"],
            "Committee_Score": result["weighted_vote"]["committee_score"],
            "Buy_Votes": result["vote_summary"]["buy_votes"],
            "Hold_Votes": result["vote_summary"]["hold_votes"],
            "Sell_Votes": result["vote_summary"]["sell_votes"],
            "Avg_Confidence": result["vote_summary"]["avg_confidence"],
            "Has_Disagreement": result["debate"]["has_disagreement"],
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False)

    print(df.tail(20))
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()