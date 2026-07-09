import pandas as pd
import json
from pathlib import Path

from src.agents.base_ai_agent import BaseAIAgent

INPUT_FILE = Path("data/processed/features_clean.csv")
OUTPUT_FILE = Path("data/processed/technical_ai_agent_outputs.csv")


def build_evidence(row):
    return {
        "ticker": row["Ticker"],
        "date": row["Date"],
        "close": row["Close"],
        "heikin_ashi_color": row["HA_Color"],
        "rsi_14": row["RSI_14"],
        "ma_50": row["MA_50"],
        "ma_200": row["MA_200"],
        "price_above_ma_200": row["Close"] > row["MA_200"],
        "ma_50_above_ma_200": row["MA_50"] > row["MA_200"],
        "momentum_10": row["Momentum_10"],
        "atr_ratio": row["ATR_Ratio"],
        "drop_from_20d_high": row["Drop_From_20D_High"],
    }


def main():
    df = pd.read_csv(INPUT_FILE)
    latest = df.sort_values("Date").groupby("Ticker").tail(1)

    agent = BaseAIAgent(
        agent_name="Technical AI Agent",
        role_description="""
You are a technical market analyst.
You evaluate Heikin Ashi candles, trend, RSI, momentum, volatility, and recent price drops.
You decide whether the technical setup supports BUY, HOLD, or SELL.
"""
    )

    outputs = []

    for _, row in latest.iterrows():
        print(f"Running Technical AI Agent for {row['Ticker']}...")

        evidence = build_evidence(row)
        result = agent.run(evidence)

        outputs.append({
            "Date": row["Date"],
            "Ticker": row["Ticker"],
            "Close": row["Close"],
            "Agent_Name": result["agent_name"],
            "Action": result["action"],
            "Confidence": result["confidence"],
            "Reasoning": result["reasoning"],
            "Risks": json.dumps(result["risks"]),
            "Evidence_Summary": result["evidence_summary"],
        })

    output_df = pd.DataFrame(outputs)
    output_df.to_csv(OUTPUT_FILE, index=False)

    print(output_df)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()