import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import errors

QUEUE_FILE = Path("data/processed/research_queue.csv")
COMMITTEE_FILE = Path("data/processed/structured_committee_summary.csv")
TECH_AI_FILE = Path("data/processed/technical_ai_agent_results.csv")
RISK_AI_FILE = Path("data/processed/risk_ai_agent_results.csv")
NEWS_FILE = Path("data/processed/news_agent_results.csv")
FUNDAMENTAL_FILE = Path("data/processed/fundamental_agent_results.csv")
RULE_PLAN_FILE = Path("data/processed/portfolio_allocation_plan.csv")

OUTPUT_FILE = Path("data/processed/portfolio_ai_plan.csv")

load_dotenv()


def load_optional_csv(path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def fallback_plan(cash, merged):
    plans = []

    for _, row in merged.iterrows():
        recommendation = row.get("Recommendation", "WATCH")
        dollar_amount = float(row.get("Dollar_Amount", 0))
        price = float(row.get("Current_Price", row.get("Close", 0)))
        shares = dollar_amount / price if price > 0 else 0

        plans.append({
            "Ticker": row["Ticker"],
            "AI_Recommendation": recommendation,
            "AI_Allocation_Dollars": dollar_amount,
            "AI_Estimated_Shares": round(shares, 4),
            "AI_Confidence": float(row.get("Opportunity_Score", 0)) / 100,
            "AI_Reason": "Fallback used. Based on rule-based portfolio allocation plan.",
            "AI_Risks": json.dumps(["No LLM portfolio reasoning available."]),
        })

    return plans


def build_context(cash, merged):
    rows = []

    for _, row in merged.iterrows():
        rows.append({
            "ticker": row["Ticker"],
            "price": float(row.get("Current_Price", row.get("Close", 0))),
            "screening_score": float(row.get("Screening_Score", 0)),
            "committee": {
                "action": row.get("Final_Action", "HOLD"),
                "score": float(row.get("Committee_Score", 0)),
                "avg_confidence": float(row.get("Avg_Confidence", 0)),
                "has_disagreement": bool(row.get("Has_Disagreement", False)),
            },
            "rule_based_portfolio_plan": {
                "recommendation": row.get("Recommendation", "WATCH"),
                "opportunity_score": float(row.get("Opportunity_Score", 0)),
                "suggested_dollars": float(row.get("Dollar_Amount", 0)),
                "reason": row.get("Reason", ""),
            },
            "technical_ai": {
                "action": row.get("Technical_AI_Action", ""),
                "confidence": row.get("Technical_AI_Confidence", ""),
                "summary": row.get("Technical_AI_Summary", ""),
                "bullish": row.get("Technical_AI_Bullish", ""),
                "bearish": row.get("Technical_AI_Bearish", ""),
                "risks": row.get("Technical_AI_Risks", ""),
            },
            "risk_ai": {
                "action": row.get("Risk_AI_Action", ""),
                "risk_level": row.get("Risk_AI_Level", ""),
                "confidence": row.get("Risk_AI_Confidence", ""),
                "summary": row.get("Risk_AI_Summary", ""),
                "risks": row.get("Risk_AI_Risks", ""),
                "mitigations": row.get("Risk_AI_Mitigations", ""),
            },
            "news": {
                "sentiment": row.get("News_Sentiment", ""),
                "confidence": row.get("News_Confidence", ""),
                "summary": row.get("News_Summary", ""),
                "positive": row.get("Positive_News", ""),
                "negative": row.get("Negative_News", ""),
                "risks": row.get("News_Risks", ""),
            },
            "fundamentals": {
                "view": row.get("Fundamental_View", ""),
                "score": row.get("Fundamental_Score", ""),
                "positives": row.get("Fundamental_Positives", ""),
                "negatives": row.get("Fundamental_Negatives", ""),
                "risks": row.get("Fundamental_Risks", ""),
            },
        })

    return {
        "available_cash": cash,
        "portfolio_constraints": {
            "max_single_position_percent": 8,
            "prefer_small_starter_positions": True,
            "avoid_high_disagreement_high_risk_names": True,
            "educational_paper_trading_only": True,
        },
        "candidate_stocks": rows,
    }


def build_prompt(context):
    return f"""
You are a Portfolio Manager AI Agent for an educational paper-trading investment committee.

Your job:
Decide which stocks, if any, should receive paper-trading capital today.

Use ONLY the provided structured evidence.
Do not invent news, fundamentals, prices, or external facts.
You may choose to hold cash if conviction is weak.
Prefer diversified, small starter positions.
Do not allocate more than 8% of available cash to one stock.
Educational paper trading only, not financial advice.

Return ONLY valid JSON:

{{
  "portfolio_summary": "short explanation of today's plan",
  "cash_to_keep": 0.0,
  "orders": [
    {{
      "ticker": "AAPL",
      "action": "BUY or WATCH or AVOID",
      "allocation_dollars": 0.0,
      "confidence": 0.0,
      "reason": "short reason",
      "risks": ["risk 1", "risk 2"]
    }}
  ]
}}

Context:
{json.dumps(context, indent=2)}
"""


def call_gemini(context):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=build_prompt(context),
        )

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except (errors.ClientError, json.JSONDecodeError, Exception) as e:
        print(f"Portfolio AI fallback used: {e}")
        return None


def main():
    cash = float(input("Enter available paper trading cash: "))

    queue = pd.read_csv(QUEUE_FILE)
    committee = pd.read_csv(COMMITTEE_FILE)
    tech_ai = load_optional_csv(TECH_AI_FILE)
    risk_ai = load_optional_csv(RISK_AI_FILE)
    news = load_optional_csv(NEWS_FILE)
    fundamentals = load_optional_csv(FUNDAMENTAL_FILE)
    rule_plan = load_optional_csv(RULE_PLAN_FILE)

    merged = queue.merge(committee, on=["Date", "Ticker"], how="left")

    if not tech_ai.empty:
        merged = merged.merge(tech_ai, on="Ticker", how="left")

    if not risk_ai.empty:
        merged = merged.merge(risk_ai, on="Ticker", how="left")

    if not news.empty:
        merged = merged.merge(news, on="Ticker", how="left")

    if not fundamentals.empty:
        merged = merged.merge(fundamentals, on=["Date", "Ticker"], how="left")

    if not rule_plan.empty:
        merged = merged.merge(rule_plan, on="Ticker", how="left", suffixes=("", "_Rule"))

    context = build_context(cash, merged)
    result = call_gemini(context)

    if result is None:
        print("Using fallback portfolio AI plan.")
        plans = fallback_plan(cash, merged)
        summary = "Fallback plan generated from rule-based portfolio allocation."
        cash_to_keep = cash - sum(p["AI_Allocation_Dollars"] for p in plans)
    else:
        summary = result.get("portfolio_summary", "")
        cash_to_keep = result.get("cash_to_keep", cash)

        plans = []
        for order in result.get("orders", []):
            ticker = order.get("ticker")
            row = merged[merged["Ticker"] == ticker]

            price = 0
            if not row.empty:
                price = float(row.iloc[0].get("Current_Price", row.iloc[0].get("Close", 0)))

            dollars = float(order.get("allocation_dollars", 0))
            shares = dollars / price if price > 0 else 0

            plans.append({
                "Ticker": ticker,
                "AI_Recommendation": order.get("action", "WATCH"),
                "AI_Allocation_Dollars": dollars,
                "AI_Estimated_Shares": round(shares, 4),
                "AI_Confidence": order.get("confidence", 0.0),
                "AI_Reason": order.get("reason", ""),
                "AI_Risks": json.dumps(order.get("risks", [])),
            })

    out = pd.DataFrame(plans)
    out["Portfolio_Summary"] = summary
    out["Cash_To_Keep"] = cash_to_keep

    out.to_csv(OUTPUT_FILE, index=False)

    print(out)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()