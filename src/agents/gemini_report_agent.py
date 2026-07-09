import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from google import genai

INPUT_FILE = Path("data/processed/executive_agent_recommendations.csv")
OUTPUT_FILE = Path("data/processed/gemini_agent_reports.csv")

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

client = genai.Client(api_key=api_key)


def build_prompt(row):
    return f"""
You are an AI portfolio manager. Use ONLY the evidence below.
Do not invent news, earnings, or outside facts.

Ticker: {row["Ticker"]}
Price: {row["Close"]}

Technical Agent:
Action: {row["Technical_Action"]}
Confidence: {row["Technical_Confidence"]}
Reason: {row["Technical_Reason"]}

ML Agent:
Action: {row["ML_Action"]}
Confidence: {row["ML_Confidence"]}
5-day up probability: {row["ML_Prob_5D_Up"]}
Reason: {row["ML_Reason"]}

Risk Agent:
Action: {row["Risk_Action"]}
Risk Level: {row["Risk_Level"]}
Confidence: {row["Risk_Confidence"]}
Reason: {row["Risk_Reason"]}

Executive Agent:
Action: {row["Executive_Action"]}
Confidence: {row["Executive_Confidence"]}
Suggested position: {row["Suggested_Position_%"]}%

Write a concise report with:
1. Final decision
2. Why
3. Main risks
4. What would change the decision
5. Position sizing note

Keep it clear for a beginner investor.
"""


def generate_report(row):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=build_prompt(row),
    )
    return response.text


def main():
    df = pd.read_csv(INPUT_FILE)
    latest = df.sort_values("Date").groupby("Ticker").tail(1).copy()

    reports = []

    for _, row in latest.iterrows():
        print(f"Generating Gemini report for {row['Ticker']}...")
        report = generate_report(row)

        reports.append({
            "Date": row["Date"],
            "Ticker": row["Ticker"],
            "Executive_Action": row["Executive_Action"],
            "Executive_Confidence": row["Executive_Confidence"],
            "Suggested_Position_%": row["Suggested_Position_%"],
            "Gemini_Report": report
        })

    pd.DataFrame(reports).to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved reports to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()