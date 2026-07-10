from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Paper Trading", layout="wide")

SUMMARY_FILE = Path("data/processed/structured_committee_summary.csv")
FEATURES_FILE = Path("data/processed/features_clean.csv")
ALLOCATION_FILE = Path("data/processed/portfolio_allocation_plan.csv")

TRADES_FILE = Path("data/processed/paper_trades.csv")
ACCOUNT_FILE = Path("data/processed/paper_account.csv")


def load_data():
    summary = pd.read_csv(SUMMARY_FILE)
    summary["Date"] = pd.to_datetime(summary["Date"])

    features = pd.read_csv(FEATURES_FILE)
    features["Date"] = pd.to_datetime(features["Date"])

    if ALLOCATION_FILE.exists():
        allocation = pd.read_csv(ALLOCATION_FILE)
    else:
        allocation = pd.DataFrame()

    return summary, features, allocation


def get_latest_prices(features):
    return features.sort_values("Date").groupby("Ticker").tail(1)[
        ["Ticker", "Date", "Close"]
    ]


def load_account():
    if ACCOUNT_FILE.exists():
        return pd.read_csv(ACCOUNT_FILE).iloc[0]
    return None


def load_trades():
    if TRADES_FILE.exists():
        return pd.read_csv(TRADES_FILE)
    return pd.DataFrame(
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


def save_account(starting_cash, cash):
    pd.DataFrame(
        [{"Starting_Cash": starting_cash, "Cash": cash}]
    ).to_csv(ACCOUNT_FILE, index=False)


def save_trades(trades):
    trades.to_csv(TRADES_FILE, index=False)


def calculate_holdings(trades):
    holdings = {}

    if trades.empty:
        return holdings

    for _, trade in trades.iterrows():
        ticker = trade["Ticker"]
        shares = float(trade["Shares"])

        if ticker not in holdings:
            holdings[ticker] = 0.0

        if trade["Action"] == "BUY":
            holdings[ticker] += shares
        elif trade["Action"] == "SELL":
            holdings[ticker] -= shares

    return {ticker: shares for ticker, shares in holdings.items() if shares > 0}


def get_price(ticker, latest_prices):
    row = latest_prices[latest_prices["Ticker"] == ticker]

    if row.empty:
        return 0.0

    return float(row["Close"].iloc[0])


def execute_trade(
    trades,
    account,
    ticker,
    action,
    shares,
    price,
    ai_action,
    ai_score,
    trade_source,
    reason,
):
    cash = float(account["Cash"])
    starting_cash = float(account["Starting_Cash"])
    trade_value = shares * price

    holdings = calculate_holdings(trades)

    if action == "BUY" and trade_value > cash:
        raise ValueError("Not enough cash for this trade.")

    if action == "SELL" and shares > holdings.get(ticker, 0):
        raise ValueError("Not enough shares to sell.")

    new_cash = cash - trade_value if action == "BUY" else cash + trade_value

    new_trade = {
        "Timestamp": pd.Timestamp.now(),
        "Ticker": ticker,
        "Action": action,
        "Shares": shares,
        "Price": price,
        "Trade_Value": trade_value,
        "AI_Action": ai_action,
        "AI_Score": ai_score,
        "Trade_Source": trade_source,
        "Reason": reason,
    }

    trades = pd.concat([trades, pd.DataFrame([new_trade])], ignore_index=True)

    save_account(starting_cash, new_cash)
    save_trades(trades)


def decision_emoji(action):
    if action in ["BUY", "SMALL BUY"]:
        return "🟢"
    if action in ["SELL", "AVOID"]:
        return "🔴"
    return "🟡"


summary, features, allocation = load_data()
latest_prices = get_latest_prices(features)

st.title("Paper Trading Simulator")
st.caption("Practice portfolio account powered by AI committee recommendations.")

account = load_account()

if account is None:
    st.subheader("Create Practice Account")

    starting_cash = st.number_input(
        "Starting cash",
        min_value=100.0,
        value=10000.0,
        step=100.0,
    )

    if st.button("Create Account", use_container_width=True):
        save_account(starting_cash, starting_cash)

        empty_trades = pd.DataFrame(
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
        save_trades(empty_trades)

        st.success("Practice account created.")
        st.rerun()

else:
    trades = load_trades()
    holdings = calculate_holdings(trades)

    cash = float(account["Cash"])
    starting_cash = float(account["Starting_Cash"])

    holdings_value = 0.0

    position_rows = []

    for ticker, shares in holdings.items():
        price = get_price(ticker, latest_prices)
        market_value = shares * price
        holdings_value += market_value

        position_rows.append(
            {
                "Ticker": ticker,
                "Shares": shares,
                "Current Price": price,
                "Market Value": market_value,
            }
        )

    total_value = cash + holdings_value
    pnl = total_value - starting_cash
    pnl_pct = pnl / starting_cash if starting_cash > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Cash", f"${cash:,.2f}")
    k2.metric("Holdings", f"${holdings_value:,.2f}")
    k3.metric("Portfolio Value", f"${total_value:,.2f}")
    k4.metric("P/L", f"${pnl:,.2f}", f"{pnl_pct:.2%}")

    st.markdown("---")

    left, right = st.columns([0.62, 0.38])

    with left:
        st.subheader("AI Portfolio Plan")

        if allocation.empty:
            st.warning(
                "No portfolio allocation plan found. Run the portfolio manager first:\n\n"
                "`python -m src.agents.portfolio.portfolio_manager`"
            )
        else:
            display_plan = allocation[
                [
                    "Ticker",
                    "Recommendation",
                    "Opportunity_Score",
                    "Allocation_%",
                    "Dollar_Amount",
                    "Estimated_Shares",
                    "Committee_Action",
                    "Current_Price",
                ]
            ].copy()

            st.dataframe(display_plan, use_container_width=True, height=280)

            buy_candidates = allocation[
                allocation["Recommendation"].isin(["BUY", "SMALL BUY"])
            ].copy()

            st.markdown("### Suggested Trades")

            if buy_candidates.empty:
                st.info("The AI does not currently recommend any buys.")
            else:
                for _, plan in buy_candidates.iterrows():
                    ticker = plan["Ticker"]
                    recommendation = plan["Recommendation"]
                    dollar_amount = float(plan["Dollar_Amount"])
                    shares = float(plan["Estimated_Shares"])
                    price = float(plan["Current_Price"])

                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns(4)

                        c1.metric("Ticker", ticker)
                        c2.metric(
                            "AI Recommendation",
                            f"{decision_emoji(recommendation)} {recommendation}",
                        )
                        c3.metric("Allocation", f"${dollar_amount:,.2f}")
                        c4.metric("Shares", f"{shares:.4f}")

                        st.caption(plan["Reason"])

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
                                    action="BUY",
                                    shares=shares,
                                    price=price,
                                    ai_action=plan["Committee_Action"],
                                    ai_score=plan["Committee_Score"],
                                    trade_source="AI Portfolio Plan",
                                    reason=plan["Reason"],
                                )

                                st.success(f"Bought {shares:.4f} shares of {ticker}.")
                                st.rerun()

                            except Exception as e:
                                st.error(str(e))

    with right:
        st.subheader("Manual Paper Trade")

        ticker = st.selectbox("Ticker", sorted(summary["Ticker"].unique()))

        latest_row = latest_prices[latest_prices["Ticker"] == ticker].iloc[0]
        price = float(latest_row["Close"])

        committee_row = summary[summary["Ticker"] == ticker].iloc[0]

        s1, s2, s3 = st.columns(3)
        s1.metric("Price", f"${price:.2f}")
        s2.metric("Committee", committee_row["Final_Action"])
        s3.metric("Score", f"{committee_row['Committee_Score']:.2f}")

        action = st.radio("Action", ["BUY", "SELL"], horizontal=True)

        dollars = st.number_input(
            "Trade amount ($)",
            min_value=0.0,
            value=500.0,
            step=100.0,
        )

        shares = dollars / price if price > 0 else 0

        st.write(f"Estimated shares: **{shares:.4f}**")

        user_reason = st.text_input(
            "Reason / note",
            placeholder="Why are you taking this trade?",
        )

        if st.button("Submit Manual Trade", use_container_width=True):
            try:
                execute_trade(
                    trades=trades,
                    account=account,
                    ticker=ticker,
                    action=action,
                    shares=shares,
                    price=price,
                    ai_action=committee_row["Final_Action"],
                    ai_score=committee_row["Committee_Score"],
                    trade_source="Manual",
                    reason=user_reason,
                )

                st.success(f"{action} trade submitted.")
                st.rerun()

            except Exception as e:
                st.error(str(e))

        st.markdown("---")

        st.subheader("Current Holdings")

        if position_rows:
            positions_df = pd.DataFrame(position_rows)
            st.dataframe(positions_df, use_container_width=True, height=220)
        else:
            st.info("No positions yet.")

    st.markdown("---")

    st.subheader("Paper Trail")

    if trades.empty:
        st.info("No trades yet.")
    else:
        display_trades = trades.sort_values("Timestamp", ascending=False)
        st.dataframe(display_trades, use_container_width=True, height=350)