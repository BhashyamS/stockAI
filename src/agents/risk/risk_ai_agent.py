import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import errors

QUEUE_FILE = Path("data/processed/research_queue.csv")
FEATURES_FILE = Path("data/processed/features_clean.csv")
OUTPUT_FILE = Path("data/processed/risk_ai_agent_results.csv")

load_dotenv()


def fallback_response(row):
    return {
        "Ticker": row["Ticker"],
        "Risk_AI_Action": "HOLD",
        "Risk_AI_Level": "UNKNOWN",
        "Risk_AI_Confidence": 0.0,
        "Risk_AI_Summary": "Gemini unavailable. Fallback used.",
        "Risk_AI_Risks": json.dumps(["No AI risk reasoning available."]),
        "Risk_AI_Mitigations": json.dumps([]),
    }


def build_context(row):
    return {
        "ticker": row["Ticker"],
        "date": row["Date"],
        "price": row["Close"],
        "trend": {
            "price_above_ma200": bool(row["Close"] > row["MA_200"]),
            "ma50_above_ma200": bool(row["MA_50"] > row["MA_200"]),
            "momentum_10": row["Momentum_10"],
            "drop_from_20d_high": row["Drop_From_20D_High"],
        },
        "volatility": {
            "atr_14": row["ATR_14"],
            "atr_ratio": row["ATR_Ratio"],
            "volatility_20": row["Volatility_20"],
        },
        "technical_stress": {
            "rsi_14": row["RSI_14"],
            "ha_color": row["HA_Color"],
        },
    }


def build_prompt(context):
    return f"""
You are a Risk Manager inside an AI investment committee.

Analyze downside risk using ONLY the provided evidence.
Do not use outside news or facts.
Do not make a buy thesis.
Educational analysis only, not financial advice.

Return ONLY valid JSON:

{{
  "ticker": "{context['ticker']}",
  "risk_action": "BUY or HOLD or SELL",
  "risk_level": "LOW or MEDIUM or HIGH",
  "confidence": 0.0,
  "summary": "short dashboard-friendly risk summary",
  "risks": ["risk 1", "risk 2"],
  "mitigations": ["mitigation 1", "mitigation 2"]
}}

Risk evidence:
{json.dumps(context, indent=2)}
"""


def call_gemini(row):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return fallback_response(row)

    client = genai.Client(api_key=api_key)
    context = build_context(row)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=build_prompt(context),
        )

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)

        return {
            "Ticker": row["Ticker"],
            "Risk_AI_Action": result.get("risk_action", "HOLD"),
            "Risk_AI_Level": result.get("risk_level", "MEDIUM"),
            "Risk_AI_Confidence": result.get("confidence", 0.0),
            "Risk_AI_Summary": result.get("summary", ""),
            "Risk_AI_Risks": json.dumps(result.get("risks", [])),
            "Risk_AI_Mitigations": json.dumps(result.get("mitigations", [])),
        }

    except (errors.ClientError, json.JSONDecodeError, Exception) as e:
        print(f"Risk AI fallback for {row['Ticker']}: {e}")
        return fallback_response(row)


def main():
    queue = pd.read_csv(QUEUE_FILE)
    features = pd.read_csv(FEATURES_FILE)

    latest = features.sort_values("Date").groupby("Ticker").tail(1)

    outputs = []

    for ticker in queue["Ticker"].head(5):
        row_df = latest[latest["Ticker"] == ticker]

        if row_df.empty:
            print(f"No feature data for {ticker}")
            continue

        row = row_df.iloc[0]
        print(f"Running Risk AI Agent for {ticker}...")
        outputs.append(call_gemini(row))

    out = pd.DataFrame(outputs)
    out.to_csv(OUTPUT_FILE, index=False)

    print(out)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()