import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Strategy Documentation", layout="wide")

st.title("StockAI Strategy Documentation")
st.caption("Understand exactly how each strategy buys, sells, gains, and loses money.")

DATA_DIR = Path("data/processed")

STRATEGIES = ["TrendFollowingV2", "TrendFollowingV3", "RiskAwareTrendV4"]


@st.cache_data
def load_backtests():
    frames = []

    for strategy in STRATEGIES:
        path = DATA_DIR / f"{strategy}_backtest_results.csv"
        df = pd.read_csv(path)
        df["Date"] = pd.to_datetime(df["Date"])
        df["Strategy"] = strategy
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


@st.cache_data
def load_trades():
    frames = []

    for strategy in STRATEGIES:
        path = DATA_DIR / f"{strategy}_trade_log.csv"
        df = pd.read_csv(path)

        if df.empty:
            continue

        df["Entry_Date"] = pd.to_datetime(df["Entry_Date"])
        df["Exit_Date"] = pd.to_datetime(df["Exit_Date"])
        df["Strategy"] = strategy
        df["Trade_Return_%"] = df["Trade_Return"] * 100
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


@st.cache_data
def load_scorecards():
    frames = []

    for strategy in STRATEGIES:
        path = DATA_DIR / f"{strategy}_scorecard.csv"
        df = pd.read_csv(path)
        df["Strategy"] = strategy
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


backtests = load_backtests()
trades = load_trades()
scorecards = load_scorecards()

st.sidebar.header("Filters")

selected_strategy = st.sidebar.selectbox("Strategy", STRATEGIES)
tickers = sorted(backtests["Ticker"].unique())
selected_ticker = st.sidebar.selectbox("Ticker", tickers)

ticker_backtest = backtests[
    (backtests["Ticker"] == selected_ticker)
    & (backtests["Strategy"] == selected_strategy)
].copy()

ticker_trades = trades[
    (trades["Ticker"] == selected_ticker)
    & (trades["Strategy"] == selected_strategy)
].copy()

ticker_scorecard = scorecards[
    (scorecards["Ticker"] == selected_ticker)
    & (scorecards["Strategy"] == selected_strategy)
].iloc[0]

st.header(f"{selected_strategy} on {selected_ticker}")

st.markdown(
    """
    This page explains the full backtest step-by-step.

    The system starts with **$10,000** for each stock and strategy.
    When the strategy says **BUY**, it invests the available cash.
    When the strategy says **SELL**, it exits the position and returns to cash.
    Trades include estimated transaction cost and slippage.
    """
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Starting Cash", "$10,000")
col2.metric("Final Value", f"${ticker_scorecard['Strategy_Final']:,.2f}")
col3.metric("Total Return", f"{ticker_scorecard['Strategy_Return_%']:.2f}%")
col4.metric("Max Drawdown", f"{ticker_scorecard['Strategy_MaxDD_%']:.2f}%")

col5, col6, col7, col8 = st.columns(4)

winning_trades = ticker_trades[ticker_trades["Trade_Return_%"] > 0]
losing_trades = ticker_trades[ticker_trades["Trade_Return_%"] <= 0]

win_rate = (
    len(winning_trades) / len(ticker_trades) * 100
    if len(ticker_trades) > 0
    else 0
)

col5.metric("Number of Trades", len(ticker_trades))
col6.metric("Winning Trades", len(winning_trades))
col7.metric("Losing Trades", len(losing_trades))
col8.metric("Win Rate", f"{win_rate:.2f}%")

st.markdown("---")

st.subheader("Portfolio Value Over Time")

fig_equity = px.line(
    ticker_backtest,
    x="Date",
    y="Portfolio_Value",
    title=f"{selected_strategy} portfolio value for {selected_ticker}",
)

st.plotly_chart(fig_equity, use_container_width=True)

st.subheader("Where the Strategy Bought and Sold")

price_data = ticker_backtest.copy()

fig_price = px.line(
    price_data,
    x="Date",
    y="Close",
    title=f"{selected_ticker} price with buy and sell points",
)

if not ticker_trades.empty:
    buys = ticker_trades[["Entry_Date", "Entry_Price"]].rename(
        columns={"Entry_Date": "Date", "Entry_Price": "Price"}
    )
    sells = ticker_trades[["Exit_Date", "Exit_Price"]].rename(
        columns={"Exit_Date": "Date", "Exit_Price": "Price"}
    )

    fig_price.add_scatter(
        x=buys["Date"],
        y=buys["Price"],
        mode="markers",
        name="Buy",
        marker=dict(size=10, symbol="triangle-up"),
    )

    fig_price.add_scatter(
        x=sells["Date"],
        y=sells["Price"],
        mode="markers",
        name="Sell",
        marker=dict(size=10, symbol="triangle-down"),
    )

st.plotly_chart(fig_price, use_container_width=True)

st.subheader("Trade-by-Trade Documentation")

st.markdown(
    """
    Each row below is one completed trade.

    - **Entry Date** = when the strategy bought
    - **Exit Date** = when the strategy sold
    - **Entry Price** = simulated buy price
    - **Exit Price** = simulated sell price
    - **Trade Return %** = percentage gain/loss on that trade
    - **Profit** = estimated portfolio profit/loss after exiting
    """
)

if ticker_trades.empty:
    st.warning("No completed trades for this strategy and ticker.")
else:
    display_trades = ticker_trades.copy()
    display_trades["Entry_Price"] = display_trades["Entry_Price"].round(2)
    display_trades["Exit_Price"] = display_trades["Exit_Price"].round(2)
    display_trades["Trade_Return_%"] = display_trades["Trade_Return_%"].round(2)
    display_trades["Profit"] = display_trades["Profit"].round(2)

    st.dataframe(
        display_trades[
            [
                "Strategy",
                "Ticker",
                "Entry_Date",
                "Exit_Date",
                "Entry_Price",
                "Exit_Price",
                "Trade_Return_%",
                "Profit",
            ]
        ],
        use_container_width=True,
    )

st.subheader("Biggest Gains and Losses")

gain_loss_cols = st.columns(2)

with gain_loss_cols[0]:
    st.markdown("### Biggest Winning Trades")
    if not ticker_trades.empty:
        st.dataframe(
            ticker_trades.sort_values("Trade_Return_%", ascending=False)
            .head(5)[
                [
                    "Entry_Date",
                    "Exit_Date",
                    "Entry_Price",
                    "Exit_Price",
                    "Trade_Return_%",
                    "Profit",
                ]
            ],
            use_container_width=True,
        )

with gain_loss_cols[1]:
    st.markdown("### Biggest Losing Trades")
    if not ticker_trades.empty:
        st.dataframe(
            ticker_trades.sort_values("Trade_Return_%", ascending=True)
            .head(5)[
                [
                    "Entry_Date",
                    "Exit_Date",
                    "Entry_Price",
                    "Exit_Price",
                    "Trade_Return_%",
                    "Profit",
                ]
            ],
            use_container_width=True,
        )

st.subheader("Why This Strategy Made or Lost Money")

if len(ticker_trades) > 0:
    avg_win = winning_trades["Trade_Return_%"].mean() if len(winning_trades) else 0
    avg_loss = losing_trades["Trade_Return_%"].mean() if len(losing_trades) else 0

    st.markdown(
        f"""
        For **{selected_ticker}**, the **{selected_strategy}** strategy completed
        **{len(ticker_trades)} trades**.

        It won **{len(winning_trades)}** trades and lost **{len(losing_trades)}** trades.

        The average winning trade returned **{avg_win:.2f}%**.
        The average losing trade returned **{avg_loss:.2f}%**.

        The ending portfolio value was **${ticker_scorecard['Strategy_Final']:,.2f}**,
        starting from **$10,000**.
        """
    )

st.subheader("Compare Against Buy & Hold")

comparison = pd.DataFrame(
    {
        "Approach": ["Strategy", "Buy & Hold"],
        "Final Value": [
            ticker_scorecard["Strategy_Final"],
            ticker_scorecard["BuyHold_Final"],
        ],
        "Total Return %": [
            ticker_scorecard["Strategy_Return_%"],
            ticker_scorecard["BuyHold_Return_%"],
        ],
        "Sharpe Ratio": [
            ticker_scorecard["Strategy_Sharpe"],
            ticker_scorecard["BuyHold_Sharpe"],
        ],
        "Max Drawdown %": [
            ticker_scorecard["Strategy_MaxDD_%"],
            ticker_scorecard["BuyHold_MaxDD_%"],
        ],
    }
)

st.dataframe(comparison, use_container_width=True)

fig_compare = px.bar(
    comparison,
    x="Approach",
    y="Total Return %",
    text="Total Return %",
    title="Strategy vs Buy & Hold Return",
)

fig_compare.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

st.plotly_chart(fig_compare, use_container_width=True)