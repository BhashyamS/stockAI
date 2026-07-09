import os
import json
import argparse
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import errors

INPUT_FILE = Path("data/processed/investment_committee_report.csv")
OUTPUT_FILE = Path("data/processed/cio_gemini_memos.csv")

load_dotenv()


def build_evidence(row):
    return {
        "ticker": row["Ticker"],
        "date": row["Date"],
        "price": round(row["Close"], 2),
        "technical": {
            "action": row["Technical_Action"],
            "confidence": row["Technical_Confidence"],
            "reason": row["Technical_Reason"],
        },
        "ml": {
            "action": row["ML_Action"],
            "confidence": row["ML_Confidence"],
            "probability_5d_up": row["ML_Prob_5D_Up"],
            "reason": row["ML_Reason"],
        },
        "risk": {
            "action": row["Risk_Action"],
            "risk_level": row["Risk_Level"],
            "confidence": row["Risk_Confidence"],
            "reason": row["Risk_Reason"],
        },
        "executive_engine": {
            "action": row["Executive_Action"],
            "confidence": row["Executive_Confidence"],
            "position_size_percent": row["Suggested_Position_%"],
        },
    }


def build_prompt(evidence):
    return f"""
You are the CIO of an AI investment committee.

Use ONLY this evidence.
Do not invent outside facts.
Educational analysis only, not financial advice.

Return ONLY valid JSON:

{{
  "ticker": "{evidence['ticker']}",
  "final_decision": "BUY or HOLD or SELL",
  "confidence": 0.0,
  "position_size_percent": 0.0,
  "investment_memo": "short clear explanation",
  "key_reasons": ["reason 1", "reason 2"],
  "main_risks": ["risk 1", "risk 2"],
  "what_would_change_decision": ["condition 1", "condition 2"]
}}

Evidence:
{json.dumps(evidence, indent=2)}
"""


def call_gemini(evidence):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=build_prompt(evidence),
        )

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except errors.ClientError as e:
        print("Gemini quota/API error. Using fallback memo.")

        return {
            "ticker": evidence["ticker"],
            "final_decision": evidence["executive_engine"]["action"],
            "confidence": evidence["executive_engine"]["confidence"],
            "position_size_percent": evidence["executive_engine"]["position_size_percent"],
            "investment_memo": (
                "Gemini was unavailable due to API quota limits, so this memo uses the "
                "deterministic investment committee output. The decision is based on the "
                "Technical Agent, ML Agent, and Risk Agent evidence."
            ),
            "key_reasons": [
                f"Technical Agent: {evidence['technical']['action']}",
                f"ML Agent: {evidence['ml']['action']}",
                f"Risk Agent: {evidence['risk']['action']} / {evidence['risk']['risk_level']} risk",
            ],
            "main_risks": [
                evidence["risk"]["reason"]
            ],
            "what_would_change_decision": [
                "A stronger ML probability signal",
                "Improved technical trend confirmation",
                "Lower risk score or volatility"
            ],
        }


def load_existing():
    if OUTPUT_FILE.exists():
        return pd.read_csv(OUTPUT_FILE)
    return pd.DataFrame()


def main():
    print("CIO Gemini agent started")

    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    args = parser.parse_args()

    ticker = args.ticker.upper()

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing {INPUT_FILE}. Run investment_committee.py first.")

    df = pd.read_csv(INPUT_FILE)
    latest = df.sort_values("Date").groupby("Ticker").tail(1)

    row_df = latest[latest["Ticker"] == ticker]

    if row_df.empty:
        raise ValueError(f"No data found for ticker {ticker}")

    row = row_df.iloc[0]
    existing = load_existing()

    if not existing.empty:
        cached = existing[
            (existing["Ticker"] == ticker)
            & (existing["Date"] == row["Date"])
        ]

        if not cached.empty:
            print(f"Using cached CIO memo for {ticker}")
            print(cached[["Ticker", "Final_Decision", "Confidence", "Position_Size_%"]])
            return

    print(f"Calling Gemini CIO for {ticker}...")

    evidence = build_evidence(row)
    result = call_gemini(evidence)

    new_row = {
        "Date": row["Date"],
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
    out.to_csv(OUTPUT_FILE, index=False)

    print(pd.DataFrame([new_row])[["Ticker", "Final_Decision", "Confidence", "Position_Size_%"]])
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()