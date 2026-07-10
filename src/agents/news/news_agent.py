import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import errors

QUEUE_FILE = Path("data/processed/research_queue.csv")
OUTPUT_FILE = Path("data/processed/news_agent_results.csv")

load_dotenv()


def fallback_news(ticker):
    return {
        "Ticker": ticker,
        "News_Sentiment": "NEUTRAL",
        "News_Confidence": 0.0,
        "News_Summary": "News agent fallback used. No Gemini news analysis was generated.",
        "Positive_News": json.dumps([]),
        "Negative_News": json.dumps([]),
        "News_Risks": json.dumps(["No external news context available."]),
    }


def build_prompt(ticker):
    return f"""
You are a News Intelligence Agent for an AI investment committee.

Analyze recent material market/news context for {ticker}.
Focus only on investment-relevant developments:
earnings, guidance, AI/product announcements, lawsuits, regulation, macro sensitivity, major partnerships, leadership changes.

Do not make a buy/sell decision.
Return ONLY valid JSON:

{{
  "ticker": "{ticker}",
  "sentiment": "BULLISH or NEUTRAL or BEARISH",
  "confidence": 0.0,
  "summary": "short dashboard-friendly summary",
  "positive_news": ["item 1", "item 2"],
  "negative_news": ["item 1", "item 2"],
  "risks": ["risk 1", "risk 2"]
}}
"""


def call_gemini(ticker):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return fallback_news(ticker)

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=build_prompt(ticker),
        )

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)

        return {
            "Ticker": ticker,
            "News_Sentiment": result.get("sentiment", "NEUTRAL"),
            "News_Confidence": result.get("confidence", 0.0),
            "News_Summary": result.get("summary", ""),
            "Positive_News": json.dumps(result.get("positive_news", [])),
            "Negative_News": json.dumps(result.get("negative_news", [])),
            "News_Risks": json.dumps(result.get("risks", [])),
        }

    except (errors.ClientError, json.JSONDecodeError, Exception) as e:
        print(f"News agent fallback for {ticker}: {e}")
        return fallback_news(ticker)


def main():
    queue = pd.read_csv(QUEUE_FILE)

    outputs = []

    for ticker in queue["Ticker"].head(5):
        print(f"Running News Agent for {ticker}...")
        outputs.append(call_gemini(ticker))

    out = pd.DataFrame(outputs)
    out.to_csv(OUTPUT_FILE, index=False)

    print(out)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()