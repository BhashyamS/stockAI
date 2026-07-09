import pandas as pd
from pathlib import Path

FILES = [
    "TrendFollowingV2_scorecard.csv",
    "TrendFollowingV3_scorecard.csv",
    "RiskAwareTrendV4_scorecard.csv",
]

def main():
    rows = []

    for file in FILES:
        strategy_name = file.replace("_scorecard.csv", "")
        df = pd.read_csv(Path("data/processed") / file)

        rows.append({
            "Strategy": strategy_name,
            "Avg_Strategy_Return_%": df["Strategy_Return_%"].mean(),
            "Avg_BuyHold_Return_%": df["BuyHold_Return_%"].mean(),
            "Avg_Return_Outperformance_%": df["Return_Outperformance_%"].mean(),
            "Avg_Strategy_Sharpe": df["Strategy_Sharpe"].mean(),
            "Avg_BuyHold_Sharpe": df["BuyHold_Sharpe"].mean(),
            "Avg_MaxDD_%": df["Strategy_MaxDD_%"].mean(),
        })

    comparison = pd.DataFrame(rows)
    comparison.to_csv("data/processed/strategy_comparison.csv", index=False)

    print(comparison)
    print("\nSaved to data/processed/strategy_comparison.csv")


if __name__ == "__main__":
    main()