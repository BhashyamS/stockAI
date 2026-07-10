from pathlib import Path
import pandas as pd

SCREENER_FILE = Path("data/processed/market_screener_results.csv")
OUTPUT_FILE = Path("data/processed/research_queue.csv")


def priority_level(score):
    if score >= 75:
        return "HIGH"
    if score >= 55:
        return "MEDIUM"
    return "LOW"


def main(top_n=10):
    df = pd.read_csv(SCREENER_FILE)

    queue = df.sort_values("Screening_Score", ascending=False).head(top_n).copy()

    queue["Research_Priority"] = queue["Screening_Score"].apply(priority_level)
    queue["Assigned_Agents"] = "Technical Agent; ML Agent; Risk Agent; News Agent; Portfolio Agent"
    queue["Research_Status"] = "PENDING"

    queue[
        [
            "Date",
            "Ticker",
            "Close",
            "Screening_Score",
            "Research_Priority",
            "Assigned_Agents",
            "Research_Status",
            "Screening_Reason",
        ]
    ].to_csv(OUTPUT_FILE, index=False)

    print(queue[["Ticker", "Screening_Score", "Research_Priority", "Research_Status"]])
    print(f"\nSaved research queue to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()