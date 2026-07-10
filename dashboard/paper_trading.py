from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="StockAI Terminal", layout="wide")

SUMMARY_FILE = Path("data/processed/structured_committee_summary.csv")
FEATURES_FILE = Path("data/processed/features_clean.csv")
AI_PLAN_FILE = Path("data/processed/portfolio_ai_plan.csv")
TRADES_FILE = Path("data/processed/paper_trades.csv")
ACCOUNT_FILE = Path("data/processed/paper_account.csv")


def load_csv(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def save_account(starting_cash, cash):
    pd.DataFrame([{"Starting_Cash": starting_cash, "Cash": cash}]).to_csv(
        ACCOUNT_FILE, index=False
    )


def save_trades(trades):
    trades.to_csv(TRADES_FILE, index=False)


def calculate_holdings(trades):
    holdings = {}

    if trades.empty:
        return holdings

    for _, trade in trades.iterrows():
        ticker = trade["Ticker"]
        shares = float(trade["Shares"])

        holdings.setdefault(ticker, 0)

        if trade["Action"] == "BUY":
            holdings[ticker] += shares
        elif trade["Action"] == "SELL":
            holdings[ticker] -= shares

    return {k: v for k, v in holdings.items() if v > 0}


def get_latest_prices(features):
    return features.sort_values("Date").groupby("Ticker").tail(1)


def get_price(ticker, latest_prices):
    row = latest_prices[latest_prices["Ticker"] == ticker]
    return float(row["Close"].iloc[0]) if not row.empty else 0.0


def emoji(value):
    if value in ["BUY", "SMALL BUY"]:
        return "🟢"
    if value in ["SELL", "AVOID"]:
        return "🔴"
    return "🟡"


def execute_trade(trades, account, ticker, shares, price, reason, source):
    cash = float(account["Cash"])
    starting_cash = float(account["Starting_Cash"])
    trade_value = shares * price

    if trade_value > cash:
        raise ValueError("Not enough cash.")

    new_trade = {
        "Timestamp": pd.Timestamp.now(),
        "Ticker": ticker,
        "Action": "BUY",
        "Shares": shares,
        "Price": price,
        "Trade_Value": trade_value,
        "AI_Action": "BUY",
        "AI_Score": 0,
        "Trade_Source": source,
        "Reason": reason,
    }

    trades = pd.concat([trades, pd.DataFrame([new_trade])], ignore_index=True)

    save_account(starting_cash, cash - trade_value)
    save_trades(trades)


summary = load_csv(SUMMARY_FILE)
features = load_csv(FEATURES_FILE)
ai_plan = load_csv(AI_PLAN_FILE)
trades = load_csv(TRADES_FILE)
account = load_csv(ACCOUNT_FILE)

if not features.empty:
    features["Date"] = pd.to_datetime(features["Date"])

latest_prices = get_latest_prices(features) if not features.empty else pd.DataFrame()

st.title("StockAI Terminal")
st.caption("AI-managed paper fund powered by multi-agent investment research.")

if account.empty:
    st.subheader("Create AI Fund Account")

    starting_cash = st.number_input(
        "Starting cash",
        min_value=100.0,
        value=10000.0,
        step=100.0,
    )

    if st.button("Create Fund", use_container_width=True):
        save_account(starting_cash, starting_cash)
        save_trades(
            pd.DataFrame(
                columns=[
                    "Timestamp",
                    "Ticker",
                    "Action",
                    "Shares",
                    "Price",
                    "Trade_Value",
                    "AI_Action",
                    "AI_Score",
                    "Trade_Source",
                    "Reason",
                ]
            )
        )
        st.rerun()

    st.stop()

account = account.iloc[0]
holdings = calculate_holdings(trades)

cash = float(account["Cash"])
starting_cash = float(account["Starting_Cash"])

positions = []
holdings_value = 0

for ticker, shares in holdings.items():
    price = get_price(ticker, latest_prices)
    value = shares * price
    holdings_value += value

    positions.append(
        {
            "Ticker": ticker,
            "Shares": shares,
            "Price": price,
            "Value": value,
        }
    )

portfolio_value = cash + holdings_value
pnl = portfolio_value - starting_cash
pnl_pct = pnl / starting_cash if starting_cash else 0

k1, k2, k3, k4 = st.columns(4)

k1.metric("Fund Value", f"${portfolio_value:,.2f}", f"{pnl_pct:.2%}")
k2.metric("Cash", f"${cash:,.2f}")
k3.metric("Invested", f"${holdings_value:,.2f}")
k4.metric("Open Positions", len(positions))

st.markdown("---")

left, right = st.columns([0.62, 0.38])

with left:
    st.subheader("Today’s AI Fund Plan")

    if ai_plan.empty:
        st.warning("No AI portfolio plan found. Run `python -m src.agents.portfolio.portfolio_ai_agent`.")
    else:
        st.info(ai_plan["Portfolio_Summary"].iloc[0])

        st.markdown("### AI Decisions")

        for _, row in ai_plan.iterrows():
            ticker = row["Ticker"]
            rec = row["AI_Recommendation"]
            dollars = float(row["AI_Allocation_Dollars"])
            shares = float(row["AI_Estimated_Shares"])
            confidence = float(row["AI_Confidence"])
            reason = row["AI_Reason"]
            price = get_price(ticker, latest_prices)

            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([0.18, 0.22, 0.25, 0.35])

                c1.markdown(f"### {ticker}")
                c2.markdown(f"### {emoji(rec)} {rec}")
                c3.metric("Allocation", f"${dollars:,.2f}")
                c4.metric("Confidence", f"{confidence:.0%}")

                st.caption(reason)

                if dollars > 0 and shares > 0:
                    if st.button(
                        f"Accept AI Trade: Buy {ticker}",
                        key=f"accept_{ticker}",
                        use_container_width=True,
                    ):
                        try:
                            execute_trade(
                                trades=trades,
                                account=account,
                                ticker=ticker,
                                shares=shares,
                                price=price,
                                reason=reason,
                                source="AI Portfolio Manager",
                            )
                            st.success(f"Bought {shares:.4f} shares of {ticker}.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

with right:
    st.subheader("Portfolio Allocation")

    allocation_rows = []

    if cash > 0:
        allocation_rows.append({"Asset": "Cash", "Value": cash})

    for pos in positions:
        allocation_rows.append(
            {
                "Asset": pos["Ticker"],
                "Value": pos["Value"],
            }
        )

    if allocation_rows:
        allocation_df = pd.DataFrame(allocation_rows)

        fig_alloc = px.pie(
            allocation_df,
            names="Asset",
            values="Value",
            hole=0.45,
        )

        fig_alloc.update_layout(height=320, margin=dict(l=5, r=5, t=5, b=5))
        st.plotly_chart(fig_alloc, use_container_width=True)

    st.subheader("Current Positions")

    if positions:
        for pos in positions:
            with st.container(border=True):
                st.markdown(f"### {pos['Ticker']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Shares", f"{pos['Shares']:.4f}")
                c2.metric("Price", f"${pos['Price']:.2f}")
                c3.metric("Value", f"${pos['Value']:,.2f}")
    else:
        st.info("No positions yet.")

st.markdown("---")

bottom_left, bottom_right = st.columns([0.5, 0.5])

with bottom_left:
    st.subheader("Market Watchlist")

    if not summary.empty:
        display = summary[
            [
                "Ticker",
                "Final_Action",
                "Committee_Score",
                "Avg_Confidence",
                "Has_Disagreement",
            ]
        ].copy()

        fig_heatmap = px.imshow(
            display.set_index("Ticker")[
                ["Committee_Score", "Avg_Confidence", "Has_Disagreement"]
            ],
            text_auto=".2f",
            aspect="auto",
        )

        fig_heatmap.update_layout(height=310, margin=dict(l=5, r=5, t=5, b=5))
        st.plotly_chart(fig_heatmap, use_container_width=True)

with bottom_right:
    st.subheader("AI Paper Trail")

    if trades.empty:
        st.info("No trades yet.")
    else:
        recent = trades.sort_values("Timestamp", ascending=False).head(8)

        for _, trade in recent.iterrows():
            with st.container(border=True):
                st.markdown(
                    f"**{trade['Action']} {trade['Ticker']}** — "
                    f"${float(trade['Trade_Value']):,.2f}"
                )
                st.caption(trade["Reason"])