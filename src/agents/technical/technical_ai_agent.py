import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import errors

QUEUE_FILE = Path("data/processed/research_queue.csv")
FEATURES_FILE = Path("data/processed/features_clean.csv")
OUTPUT_FILE = Path("data/processed/technical_ai_agent_results.csv")

load_dotenv()


def fallback_response(row):
    return {
        "Ticker": row["Ticker"],
        "Technical_AI_Action": "HOLD",
        "Technical_AI_Confidence": 0.0,
        "Technical_AI_Summary": "Gemini unavailable. Fallback used.",
        "Technical_AI_Bullish": json.dumps([]),
        "Technical_AI_Bearish": json.dumps([]),
        "Technical_AI_Risks": json.dumps(["No AI technical reasoning available."]),
    }


def build_context(row):
    return {
        "ticker": row["Ticker"],
        "date": row["Date"],
        "close": row["Close"],
        "open": row["Open"],
        "high": row["High"],
        "low": row["Low"],
        "volume": row["Volume"],
        "heikin_ashi": {
            "color": row["HA_Color"],
            "body_ratio": row["HA_Body_Ratio"],
        },
        "trend": {
            "ma_5": row["MA_5"],
            "ma_20": row["MA_20"],
            "ma_50": row["MA_50"],
            "ma_200": row["MA_200"],
            "price_above_ma200": bool(row["Close"] > row["MA_200"]),
            "ma50_above_ma200": bool(row["MA_50"] > row["MA_200"]),
        },
        "momentum": {
            "daily_return": row["Daily_Return"],
            "momentum_10": row["Momentum_10"],
            "rsi_14": row["RSI_14"],
        },
        "risk_volatility": {
            "atr_14": row["ATR_14"],
            "atr_ratio": row["ATR_Ratio"],
            "volatility_20": row["Volatility_20"],
            "drop_from_20d_high": row["Drop_From_20D_High"],
        },
    }


def build_prompt(context):
    return f"""
You are a senior technical analyst inside an AI investment committee.

Analyze this stock using ONLY the provided technical evidence.
Do not use outside news or facts.
Do not make up prices.
Educational analysis only, not financial advice.

Return ONLY valid JSON in this schema:

{{
  "ticker": "{context['ticker']}",
  "action": "BUY or HOLD or SELL",
  "confidence": 0.0,
  "summary": "short dashboard-friendly technical summary",
  "bullish_evidence": ["reason 1", "reason 2"],
  "bearish_evidence": ["reason 1", "reason 2"],
  "risks": ["risk 1", "risk 2"]
}}

Technical evidence:
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
            "Technical_AI_Action": result.get("action", "HOLD"),
            "Technical_AI_Confidence": result.get("confidence", 0.0),
            "Technical_AI_Summary": result.get("summary", ""),
            "Technical_AI_Bullish": json.dumps(result.get("bullish_evidence", [])),
            "Technical_AI_Bearish": json.dumps(result.get("bearish_evidence", [])),
            "Technical_AI_Risks": json.dumps(result.get("risks", [])),
        }

    except (errors.ClientError, json.JSONDecodeError, Exception) as e:
        print(f"Technical AI fallback for {row['Ticker']}: {e}")
        return fallback_response(row)


def main():
    queue = pd.read_csv(QUEUE_FILE)
    features = pd.read_csv(FEATURES_FILE)

    latest = features.sort_values("Date").groupby("Ticker").tail(1)

    outputs = []

    # limit to top 5 to protect Gemini quota
    for ticker in queue["Ticker"].head(5):
        row_df = latest[latest["Ticker"] == ticker]

        if row_df.empty:
            print(f"No feature data for {ticker}")
            continue

        row = row_df.iloc[0]
        print(f"Running Technical AI Agent for {ticker}...")
        outputs.append(call_gemini(row))

    out = pd.DataFrame(outputs)
    out.to_csv(OUTPUT_FILE, index=False)

    print(out)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()