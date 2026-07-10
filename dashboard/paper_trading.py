import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Paper Trading", layout="wide")

SUMMARY_FILE = Path("data/processed/structured_committee_summary.csv")
TRADES_FILE = Path("data/processed/paper_trades.csv")
ACCOUNT_FILE = Path("data/processed/paper_account.csv")

summary = pd.read_csv(SUMMARY_FILE)
summary["Date"] = pd.to_datetime(summary["Date"])

latest = summary.sort_values("Date").groupby("Ticker").tail(1)

st.title("Paper Trading Simulator")
st.caption("Practice trading using AI committee recommendations.")

if not ACCOUNT_FILE.exists():
    st.subheader("Create Practice Account")
    starting_cash = st.number_input("Starting cash", min_value=100.0, value=10000.0, step=100.0)

    if st.button("Create Account"):
        pd.DataFrame([{"Starting_Cash": starting_cash, "Cash": starting_cash}]).to_csv(ACCOUNT_FILE, index=False)
        pd.DataFrame(columns=["Timestamp", "Ticker", "Action", "Shares", "Price", "Trade_Value", "AI_Action", "AI_Score"]).to_csv(TRADES_FILE, index=False)
        st.success("Practice account created.")
        st.rerun()

else:
    account = pd.read_csv(ACCOUNT_FILE).iloc[0]
    trades = pd.read_csv(TRADES_FILE) if TRADES_FILE.exists() else pd.DataFrame()

    ticker = st.selectbox("Ticker", sorted(latest["Ticker"].unique()))
    row = latest[latest["Ticker"] == ticker].iloc[0]

    price = 0.0
    features = pd.read_csv("data/processed/features_clean.csv")
    latest_price_row = features[features["Ticker"] == ticker].sort_values("Date").tail(1)
    if not latest_price_row.empty:
        price = float(latest_price_row["Close"].iloc[0])

    cash = float(account["Cash"])

    holdings = {}
    if not trades.empty:
        for _, t in trades.iterrows():
            holdings.setdefault(t["Ticker"], 0.0)
            if t["Action"] == "BUY":
                holdings[t["Ticker"]] += float(t["Shares"])
            else:
                holdings[t["Ticker"]] -= float(t["Shares"])

    holdings_value = 0.0
    for h_ticker, shares in holdings.items():
        latest_h = features[features["Ticker"] == h_ticker].sort_values("Date").tail(1)
        if not latest_h.empty:
            holdings_value += shares * float(latest_h["Close"].iloc[0])

    total_value = cash + holdings_value
    pnl = total_value - float(account["Starting_Cash"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cash", f"${cash:,.2f}")
    c2.metric("Holdings", f"${holdings_value:,.2f}")
    c3.metric("Portfolio Value", f"${total_value:,.2f}")
    c4.metric("P/L", f"${pnl:,.2f}")

    st.markdown("---")

    left, right = st.columns([0.55, 0.45])

    with left:
        st.subheader(f"{ticker} AI Signal")

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Decision", row["Final_Action"])
        s2.metric("Score", f"{row['Committee_Score']:.2f}")
        s3.metric("Confidence", f"{row['Avg_Confidence']:.0%}")
        s4.metric("Price", f"${price:.2f}")

        action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
        dollars = st.number_input("Trade amount ($)", min_value=0.0, value=1000.0, step=100.0)
        shares = dollars / price if price > 0 else 0

        st.write(f"Estimated shares: **{shares:.4f}**")

        if st.button("Submit Paper Trade"):
            if action == "BUY" and dollars > cash:
                st.error("Not enough cash.")
            elif action == "SELL" and shares > holdings.get(ticker, 0):
                st.error("Not enough shares.")
            else:
                trade_value = shares * price
                new_cash = cash - trade_value if action == "BUY" else cash + trade_value

                pd.DataFrame([{"Starting_Cash": account["Starting_Cash"], "Cash": new_cash}]).to_csv(ACCOUNT_FILE, index=False)

                new_trade = {
                    "Timestamp": pd.Timestamp.now(),
                    "Ticker": ticker,
                    "Action": action,
                    "Shares": shares,
                    "Price": price,
                    "Trade_Value": trade_value,
                    "AI_Action": row["Final_Action"],
                    "AI_Score": row["Committee_Score"],
                }

                trades = pd.concat([trades, pd.DataFrame([new_trade])], ignore_index=True)
                trades.to_csv(TRADES_FILE, index=False)

                st.success("Trade submitted.")
                st.rerun()

    with right:
        st.subheader("Current Holdings")

        positions = []
        for h_ticker, shares in holdings.items():
            if shares <= 0:
                continue

            latest_h = features[features["Ticker"] == h_ticker].sort_values("Date").tail(1)
            current_price = float(latest_h["Close"].iloc[0]) if not latest_h.empty else 0

            positions.append({
                "Ticker": h_ticker,
                "Shares": shares,
                "Current Price": current_price,
                "Market Value": shares * current_price,
            })

        if positions:
            st.dataframe(pd.DataFrame(positions), use_container_width=True)
        else:
            st.info("No positions yet.")

    st.markdown("---")

    st.subheader("Paper Trail")

    if not trades.empty:
        st.dataframe(trades.sort_values("Timestamp", ascending=False), use_container_width=True)
    else:
        st.info("No trades yet.")