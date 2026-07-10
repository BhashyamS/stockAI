from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="StockAI Terminal", layout="wide")

SUMMARY_FILE = Path("data/processed/structured_committee_summary.csv")
FEATURES_FILE = Path("data/processed/features_clean.csv")
AI_PLAN_FILE = Path("data/processed/portfolio_ai_plan.csv")
TRADES_FILE = Path("data/processed/paper_trades.csv")
ACCOUNT_FILE = Path("data/processed/paper_account.csv")


st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 1rem;
        }

        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.025);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 10px 12px;
            border-radius: 12px;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.55rem;
        }

        .compact-card {
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 12px;
            padding: 10px 12px;
            margin-bottom: 8px;
            background: rgba(255,255,255,0.025);
        }

        .compact-card h3 {
            margin: 0;
            font-size: 1.05rem;
        }

        .compact-card .row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        }

        .pill {
            font-size: 0.8rem;
            padding: 3px 8px;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            display: inline-block;
        }

        .small-muted {
            font-size: 0.78rem;
            opacity: 0.70;
            line-height: 1.25rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def latest_prices(features):
    return features.sort_values("Date").groupby("Ticker").tail(1)


def get_price(ticker, prices):
    row = prices[prices["Ticker"] == ticker]
    return float(row["Close"].iloc[0]) if not row.empty else 0.0


def emoji(action):
    if action in ["BUY", "SMALL BUY"]:
        return "🟢"
    if action in ["SELL", "AVOID"]:
        return "🔴"
    return "🟡"


def execute_buy(trades, account, ticker, shares, price, reason, source):
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


def range_filter(df, selected_range):
    if df.empty:
        return df

    max_date = df["Date"].max()

    if selected_range in ["1m", "15m", "1D"]:
        start = max_date - pd.DateOffset(days=5)
    elif selected_range == "5D":
        start = max_date - pd.DateOffset(days=7)
    elif selected_range == "1M":
        start = max_date - pd.DateOffset(months=1)
    elif selected_range == "3M":
        start = max_date - pd.DateOffset(months=3)
    elif selected_range == "6M":
        start = max_date - pd.DateOffset(months=6)
    elif selected_range == "1Y":
        start = max_date - pd.DateOffset(years=1)
    else:
        start = df["Date"].min()

    return df[df["Date"] >= start].copy()


def build_candlestick_chart(features, ticker, selected_range):
    ticker_features = features[features["Ticker"] == ticker].sort_values("Date").copy()
    chart_df = range_filter(ticker_features, selected_range)

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=chart_df["Date"],
            open=chart_df["Open"],
            high=chart_df["High"],
            low=chart_df["Low"],
            close=chart_df["Close"],
            name="Price",
            customdata=chart_df[["HA_Color", "RSI_14", "Momentum_10", "ATR_Ratio"]],
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Open: $%{open:.2f}<br>"
                "High: $%{high:.2f}<br>"
                "Low: $%{low:.2f}<br>"
                "Close: $%{close:.2f}<br><br>"
                "Heikin Ashi: %{customdata[0]}<br>"
                "RSI: %{customdata[1]:.1f}<br>"
                "Momentum: %{customdata[2]:.2%}<br>"
                "ATR Ratio: %{customdata[3]:.2%}"
                "<extra></extra>"
            ),
        )
    )

    if len(chart_df) > 50:
        fig.add_trace(
            go.Scatter(
                x=chart_df["Date"],
                y=chart_df["MA_50"],
                mode="lines",
                name="MA50",
            )
        )

    if len(chart_df) > 200:
        fig.add_trace(
            go.Scatter(
                x=chart_df["Date"],
                y=chart_df["MA_200"],
                mode="lines",
                name="MA200",
            )
        )

    fig.update_layout(
        title=f"{ticker} Candlestick Chart",
        height=460,
        xaxis_rangeslider_visible=True,
        yaxis_title="Price",
        margin=dict(l=8, r=8, t=42, b=8),
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1D", step="day", stepmode="backward"),
                    dict(count=5, label="5D", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
            type="date",
        ),
    )

    return fig


summary = load_csv(SUMMARY_FILE)
features = load_csv(FEATURES_FILE)
ai_plan = load_csv(AI_PLAN_FILE)
trades = load_csv(TRADES_FILE)
account_df = load_csv(ACCOUNT_FILE)

if not features.empty:
    features["Date"] = pd.to_datetime(features["Date"])

prices = latest_prices(features) if not features.empty else pd.DataFrame()

st.title("StockAI Terminal")
st.caption("AI-managed paper fund powered by a multi-agent investment committee.")

if account_df.empty:
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

account = account_df.iloc[0]
cash = float(account["Cash"])
starting_cash = float(account["Starting_Cash"])

holdings = calculate_holdings(trades)

positions = []
holdings_value = 0

for ticker, shares in holdings.items():
    price = get_price(ticker, prices)
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

buy_count = 0
watch_count = 0
avoid_count = 0

if not ai_plan.empty:
    buy_count = ai_plan["AI_Recommendation"].isin(["BUY", "SMALL BUY"]).sum()
    watch_count = (ai_plan["AI_Recommendation"] == "WATCH").sum()
    avoid_count = (ai_plan["AI_Recommendation"] == "AVOID").sum()

cash_pct = cash / portfolio_value if portfolio_value else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Fund Value", f"${portfolio_value:,.2f}", f"{pnl_pct:.2%}")
k2.metric("Cash", f"${cash:,.2f}", f"{cash_pct:.0%} cash")
k3.metric("Invested", f"${holdings_value:,.2f}")
k4.metric("Open Positions", len(positions))
k5.metric("AI Buys Today", buy_count)

st.markdown("---")

tabs = st.tabs(
    [
        "🏠 Home",
        "🤖 Committee",
        "💼 Portfolio",
        "📈 Markets",
        "💬 Ask Fund Manager",
    ]
)

with tabs[0]:
    left, right = st.columns([0.60, 0.40])

    with left:
        st.subheader("Today’s AI Decisions")

        if ai_plan.empty:
            st.warning("No AI portfolio plan found. Run the Portfolio AI Agent first.")
        else:
            st.info(ai_plan["Portfolio_Summary"].iloc[0])

            ranked_plan = ai_plan.copy()

            priority = {
                "BUY": 0,
                "SMALL BUY": 1,
                "WATCH": 2,
                "AVOID": 3,
            }

            ranked_plan["Priority"] = ranked_plan["AI_Recommendation"].map(priority).fillna(9)
            ranked_plan = ranked_plan.sort_values(
                ["Priority", "AI_Confidence", "AI_Allocation_Dollars"],
                ascending=[True, False, False],
            )

            visible_plan = ranked_plan.head(5)
            hidden_count = max(len(ranked_plan) - len(visible_plan), 0)

            for _, row in visible_plan.iterrows():
                ticker = row["Ticker"]
                rec = row["AI_Recommendation"]
                dollars = float(row["AI_Allocation_Dollars"])
                shares = float(row["AI_Estimated_Shares"])
                confidence = float(row["AI_Confidence"])
                reason = str(row["AI_Reason"])
                price = get_price(ticker, prices)

                with st.container():
                    st.markdown(
                        f"""
                        <div class="compact-card">
                            <div class="row">
                                <h3>{ticker}</h3>
                                <span class="pill">{emoji(rec)} {rec}</span>
                                <span><b>${dollars:,.0f}</b></span>
                                <span>{confidence:.0%}</span>
                            </div>
                            <div class="small-muted">{reason[:190]}{"..." if len(reason) > 190 else ""}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if dollars > 0 and shares > 0:
                        if st.button(
                            f"Accept AI Trade: Buy {ticker}",
                            key=f"home_accept_{ticker}",
                            use_container_width=True,
                        ):
                            try:
                                execute_buy(
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

            if hidden_count:
                with st.expander(f"Show {hidden_count} more decisions"):
                    for _, row in ranked_plan.tail(hidden_count).iterrows():
                        st.write(
                            f"{row['Ticker']} — {emoji(row['AI_Recommendation'])} "
                            f"{row['AI_Recommendation']} — {row['AI_Reason']}"
                        )

    with right:
        st.subheader("AI Market Stance")

        stance = "Defensive"
        if buy_count >= 3:
            stance = "Aggressive"
        elif buy_count >= 1:
            stance = "Selective"

        s1, s2, s3 = st.columns(3)
        s1.metric("Stance", stance)
        s2.metric("Cash Bias", f"{cash_pct:.0%}")
        s3.metric("Reviewed", len(ai_plan) if not ai_plan.empty else 0)

        mix = pd.DataFrame(
            [
                {"Decision": "Buy", "Count": buy_count},
                {"Decision": "Watch", "Count": watch_count},
                {"Decision": "Avoid", "Count": avoid_count},
            ]
        )

        chart1, chart2 = st.columns(2)

        with chart1:
            fig_mix = px.pie(mix, names="Decision", values="Count", hole=0.45)
            fig_mix.update_layout(height=240, margin=dict(l=5, r=5, t=5, b=5))
            st.plotly_chart(fig_mix, use_container_width=True)

        with chart2:
            allocation_rows = [{"Asset": "Cash", "Value": cash}]
            for pos in positions:
                allocation_rows.append({"Asset": pos["Ticker"], "Value": pos["Value"]})

            alloc_df = pd.DataFrame(allocation_rows)
            fig_tree = px.treemap(alloc_df, path=["Asset"], values="Value")
            fig_tree.update_layout(height=240, margin=dict(l=5, r=5, t=5, b=5))
            st.plotly_chart(fig_tree, use_container_width=True)

with tabs[1]:
    st.subheader("Committee Room")

    if summary.empty:
        st.warning("No committee summary found.")
    else:
        col1, col2 = st.columns([0.52, 0.48])

        with col1:
            st.markdown("### Committee Heatmap")

            heatmap = summary.set_index("Ticker")[
                ["Committee_Score", "Avg_Confidence", "Has_Disagreement"]
            ].copy()

            heatmap["Has_Disagreement"] = heatmap["Has_Disagreement"].astype(int)

            fig_heatmap = px.imshow(
                heatmap,
                text_auto=".2f",
                aspect="auto",
            )

            fig_heatmap.update_layout(height=390, margin=dict(l=5, r=5, t=5, b=5))
            st.plotly_chart(fig_heatmap, use_container_width=True)

        with col2:
            st.markdown("### Compact Vote Cards")

            vote_df = summary.sort_values("Committee_Score", ascending=False)

            for _, row in vote_df.iterrows():
                st.markdown(
                    f"""
                    <div class="compact-card">
                        <div class="row">
                            <h3>{row['Ticker']}</h3>
                            <span class="pill">{emoji(row['Final_Action'])} {row['Final_Action']}</span>
                            <span>Score <b>{row['Committee_Score']:.2f}</b></span>
                            <span>Conf <b>{row['Avg_Confidence']:.0%}</b></span>
                        </div>
                        <div class="small-muted">
                            Buy {row['Buy_Votes']} · Hold {row['Hold_Votes']} · Sell {row['Sell_Votes']} ·
                            Disagreement: {row['Has_Disagreement']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

with tabs[2]:
    st.subheader("Portfolio")

    left, right = st.columns([0.5, 0.5])

    with left:
        st.markdown("### Current Positions")

        if positions:
            for pos in positions:
                st.markdown(
                    f"""
                    <div class="compact-card">
                        <div class="row">
                            <h3>{pos['Ticker']}</h3>
                            <span>Shares <b>{pos['Shares']:.4f}</b></span>
                            <span>Price <b>${pos['Price']:.2f}</b></span>
                            <span>Value <b>${pos['Value']:,.2f}</b></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No positions yet.")

    with right:
        st.markdown("### Paper Trail")

        if trades.empty:
            st.info("No trades yet.")
        else:
            recent = trades.sort_values("Timestamp", ascending=False).head(10)

            for _, trade in recent.iterrows():
                reason = str(trade["Reason"])
                st.markdown(
                    f"""
                    <div class="compact-card">
                        <div class="row">
                            <h3>{trade['Action']} {trade['Ticker']}</h3>
                            <span><b>${float(trade['Trade_Value']):,.2f}</b></span>
                        </div>
                        <div class="small-muted">{reason[:180]}{"..." if len(reason) > 180 else ""}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

with tabs[3]:
    st.subheader("Markets")

    if prices.empty:
        st.warning("No market data found.")
    else:
        c1, c2 = st.columns([0.24, 0.76])

        with c1:
            selected = st.selectbox("Select ticker", sorted(prices["Ticker"].unique()))
            selected_range = st.radio(
                "Time range",
                ["1m", "15m", "1D", "5D", "1M", "3M", "6M", "1Y", "All"],
                horizontal=False,
                index=7,
            )

            ticker_features = features[features["Ticker"] == selected].sort_values("Date")
            latest = ticker_features.tail(1).iloc[0]

            st.metric("Price", f"${latest['Close']:.2f}")
            st.metric("RSI", f"{latest['RSI_14']:.1f}")
            st.metric("Momentum 10D", f"{latest['Momentum_10']:.2%}")
            st.metric("ATR Ratio", f"{latest['ATR_Ratio']:.2%}")

            if selected_range in ["1m", "15m"]:
                st.caption("Intraday data is not connected yet, so this currently falls back to recent daily candles.")

        with c2:
            st.plotly_chart(
                build_candlestick_chart(features, selected, selected_range),
                use_container_width=True,
            )

with tabs[4]:
    st.subheader("Ask the Fund Manager")

    question = st.text_input(
        "Ask about the portfolio, AI decisions, or trade plan",
        placeholder="Example: Why didn't we buy Tesla?",
    )

    if question:
        st.markdown("### Fund Manager Response")

        lower_q = question.lower()

        if "tesla" in lower_q or "tsla" in lower_q:
            tsla_row = ai_plan[ai_plan["Ticker"] == "TSLA"] if not ai_plan.empty else pd.DataFrame()

            if not tsla_row.empty:
                r = tsla_row.iloc[0]
                st.write(
                    f"TSLA was marked **{r['AI_Recommendation']}**. "
                    f"The AI reason was: {r['AI_Reason']}"
                )
            else:
                st.write("I do not have a TSLA plan available right now.")

        elif "cash" in lower_q:
            st.write(
                f"The fund is holding **${cash:,.2f} in cash**, "
                f"which is about **{cash_pct:.0%}** of the portfolio. "
                "The AI is currently being conservative because the portfolio plan does not show strong buy conviction."
            )

        elif "buy" in lower_q:
            if ai_plan.empty:
                st.write("There is no AI plan loaded yet.")
            else:
                buys = ai_plan[ai_plan["AI_Recommendation"].isin(["BUY", "SMALL BUY"])]

                if buys.empty:
                    st.write("The AI Fund Manager does not currently recommend any new buys.")
                else:
                    tickers = ", ".join(buys["Ticker"].tolist())
                    st.write(f"The AI currently recommends buying: **{tickers}**.")

        else:
            st.write(
                "I can answer questions about current AI recommendations, cash levels, holdings, "
                "and why specific stocks were marked BUY, WATCH, or AVOID."
            )