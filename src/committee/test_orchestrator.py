import pandas as pd

from src.agents.technical.opinion import TechnicalOpinionAgent
from src.agents.ml.opinion import MLOpinionAgent
from src.committee.orchestrator import InvestmentCommitteeOrchestrator

FEATURES_FILE = "data/processed/ml_predictions.csv"


def main():
    df = pd.read_csv(FEATURES_FILE)

    latest = df.sort_values("Date").groupby("Ticker").tail(1)

    agents = [
        TechnicalOpinionAgent(),
        MLOpinionAgent(),
    ]

    committee = InvestmentCommitteeOrchestrator(agents)

    for _, row in latest.iterrows():
        opinions = committee.collect_opinions(row)
        summary = committee.summarize_votes(opinions)

        print("\n" + "=" * 60)
        print(row["Ticker"])
        print(summary)


if __name__ == "__main__":
    main()