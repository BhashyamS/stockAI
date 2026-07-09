import os
import json
import argparse
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import errors

INPUT_JSON = Path("data/processed/cio_prompt_packages.json")
OUTPUT_CSV = Path("data/processed/structured_cio_memos.csv")

load_dotenv()


def build_prompt(package):
    return f"""
You are the CIO of an AI investment committee.

Use ONLY the structured committee package below.
Do not invent news, earnings, analyst ratings, or outside facts.
Educational analysis only, not financial advice.

Return ONLY valid JSON:

{{
  "ticker": "{package['ticker']}",
  "final_decision": "BUY or HOLD or SELL",
  "confidence": 0.0,
  "position_size_percent": 0.0,
  "investment_memo": "short visual-dashboard friendly memo",
  "key_reasons": ["reason 1", "reason 2"],
  "main_risks": ["risk 1", "risk 2"],
  "what_would_change_decision": ["condition 1", "condition 2"]
}}

Committee package:
{json.dumps(package, indent=2)}
"""


def fallback_memo(package):
    return {
        "ticker": package["ticker"],
        "final_decision": package["committee_decision"],
        "confidence": min(abs(package["committee_score"]) * 2, 1),
        "position_size_percent": 0.0 if package["committee_decision"] != "BUY" else 3.0,
        "investment_memo": (
            "Gemini was unavailable, so this memo uses the structured committee result. "
            "The decision is based on weighted votes from the Technical, ML, and Risk agents."
        ),
        "key_reasons": [
            f"Committee decision: {package['committee_decision']}",
            f"Committee score: {package['committee_score']}",
            package["debate"]["summary"],
        ],
        "main_risks": [
            risk
            for report in package["agent_reports"]
            for risk in report.get("risks", [])
        ][:3],
        "what_would_change_decision": [
            "Stronger agreement across agents",
            "Higher ML confidence",
            "Improved risk profile",
        ],
    }


def call_gemini(package):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return fallback_memo(package)

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=build_prompt(package),
        )

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    except (errors.ClientError, json.JSONDecodeError) as e:
        print(f"Gemini unavailable or invalid JSON. Using fallback. Error: {e}")
        return fallback_memo(package)


def load_existing():
    if OUTPUT_CSV.exists():
        return pd.read_csv(OUTPUT_CSV)
    return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    args = parser.parse_args()

    ticker = args.ticker.upper()

    with open(INPUT_JSON, "r") as f:
        packages = json.load(f)

    package = next((p for p in packages if p["ticker"] == ticker), None)

    if package is None:
        raise ValueError(f"No CIO package found for {ticker}")

    existing = load_existing()

    if not existing.empty and ticker in existing["Ticker"].values:
        print(f"Using cached structured CIO memo for {ticker}")
        print(existing[existing["Ticker"] == ticker][["Ticker", "Final_Decision", "Confidence", "Position_Size_%"]])
        return

    print(f"Running structured CIO agent for {ticker}...")

    result = call_gemini(package)

    new_row = {
        "Ticker": ticker,
        "Final_Decision": result["final_decision"],
        "Confidence": result["confidence"],
        "Position_Size_%": result["position_size_percent"],
        "Investment_Memo": result["investment_memo"],
        "Key_Reasons": json.dumps(result["key_reasons"]),
        "Main_Risks": json.dumps(result["main_risks"]),
        "What_Would_Change_Decision": json.dumps(result["what_would_change_decision"]),
    }

    out = pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True)
    out.to_csv(OUTPUT_CSV, index=False)

    print(pd.DataFrame([new_row])[["Ticker", "Final_Decision", "Confidence", "Position_Size_%"]])
    print(f"Saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()