import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="Committee Room", layout="wide")

FEATURES_FILE = Path("data/processed/features_clean.csv")
SUMMARY_FILE = Path("data/processed/structured_committee_summary.csv")
RESULTS_FILE = Path("data/processed/structured_committee_results.json")
CIO_FILE = Path("data/processed/structured_cio_memos.csv")
MEMORY_SUMMARY_FILE = Path("data/processed/committee_memory_summary.csv")


@st.cache_data
def load_data():
    features = pd.read_csv(FEATURES_FILE)
    features["Date"] = pd.to_datetime(features["Date"])

    summary = pd.read_csv(SUMMARY_FILE)
    summary["Date"] = pd.to_datetime(summary["Date"])

    with open(RESULTS_FILE, "r") as f:
        results = json.load(f)

    if CIO_FILE.exists():
        cio = pd.read_csv(CIO_FILE)
    else:
        cio = pd.DataFrame()

    if MEMORY_SUMMARY_FILE.exists():
        memory = pd.read_csv(MEMORY_SUMMARY_FILE)
        memory["Timestamp"] = pd.to_datetime(memory["Timestamp"])
    else:
        memory = pd.DataFrame()

    return features, summary, results, cio, memory


def emoji(action):
    return {"BUY": "🟢", "HOLD": "🟡", "SELL": "🔴"}.get(action, "⚪")


def get_result(results, ticker):
    for item in results:
        if item["ticker"] == ticker:
            return item
    return None


def build_chart(features, ticker, range_choice):
    df = features[features["Ticker"] == ticker].sort_values("Date").copy()
    max_date = df["Date"].max()

    ranges = {
        "1M": max_date - pd.DateOffset(months=1),
        "3M": max_date - pd.DateOffset(months=3),
        "6M": max_date - pd.DateOffset(months=6),
        "1Y": max_date - pd.DateOffset(years=1),
        "3Y": max_date - pd.DateOffset(years=3),
        "5Y": max_date - pd.DateOffset(years=5),
        "All": df["Date"].min(),
    }

    df = df[df["Date"] >= ranges[range_choice]].copy()

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            customdata=df[["HA_Color", "RSI_14", "Momentum_10", "ATR_Ratio"]],
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Open: $%{open:.2f}<br>"
                "High: $%{high:.2f}<br>"
                "Low: $%{low:.2f}<br>"
                "Close: $%{close:.2f}<br><br>"
                "HA: %{customdata[0]}<br>"
                "RSI: %{customdata[1]:.1f}<br>"
                "Momentum: %{customdata[2]:.2%}<br>"
                "ATR ratio: %{customdata[3]:.2%}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(go.Scatter(x=df["Date"], y=df["MA_50"], mode="lines", name="MA50"))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["MA_200"], mode="lines", name="MA200"))

    fig.update_layout(
        title=f"{ticker} market trend",
        height=560,
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis_rangeslider_visible=True,
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=3, label="3Y", step="year", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
            rangeslider=dict(visible=True),
            type="date",
        ),
        yaxis_title="Price",
    )

    return fig


features, summary, results, cio, memory = load_data()

st.title("AI Investment Committee Room")
st.caption("Watch specialized agents analyze, disagree, vote, and produce a CIO-ready decision.")

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = summary["Ticker"].iloc[0]

st.subheader("Portfolio Watchlist")

cols = st.columns(len(summary))

for i, (_, r) in enumerate(summary.sort_values("Ticker").iterrows()):
    with cols[i]:
        label = (
            f"{r['Ticker']}\n"
            f"{emoji(r['Final_Action'])} {r['Final_Action']}\n"
            f"{r['Avg_Confidence']:.0%}"
        )
        if st.button(label, key=f"select_{r['Ticker']}", use_container_width=True):
            st.session_state.selected_ticker = r["Ticker"]

ticker = st.session_state.selected_ticker
row = summary[summary["Ticker"] == ticker].iloc[0]
result = get_result(results, ticker)

range_choice = st.radio(
    "Chart range",
    ["1M", "3M", "6M", "1Y", "3Y", "5Y", "All"],
    horizontal=True,
    index=3,
)

st.markdown("---")

top1, top2, top3, top4, top5 = st.columns(5)

top1.metric("Selected", ticker)
top2.metric("Committee Decision", f"{emoji(row['Final_Action'])} {row['Final_Action']}")
top3.metric("Committee Score", f"{row['Committee_Score']:.2f}")
top4.metric("Avg Confidence", f"{row['Avg_Confidence']:.0%}")
top5.metric("Disagreement", "Yes" if row["Has_Disagreement"] else "No")

left, right = st.columns([0.68, 0.32])

with left:
    st.plotly_chart(build_chart(features, ticker, range_choice), use_container_width=True)

    st.subheader("Portfolio Heatmap")

    heatmap_data = summary.set_index("Ticker")[
        [
            "Committee_Score",
            "Buy_Votes",
            "Hold_Votes",
            "Sell_Votes",
            "Avg_Confidence",
            "Has_Disagreement",
        ]
    ].copy()

    heatmap_data["Has_Disagreement"] = heatmap_data["Has_Disagreement"].astype(int)

    fig_heatmap = px.imshow(
        heatmap_data,
        text_auto=".2f",
        aspect="auto",
        title="Committee score, votes, confidence, and disagreement",
    )
    fig_heatmap.update_layout(height=330, margin=dict(l=10, r=10, t=45, b=10))
    st.plotly_chart(fig_heatmap, use_container_width=True)

with right:
    st.subheader("Agent Status")

    if result:
        opinions = result["vote_summary"]["opinions"]

        for opinion in opinions:
            st.markdown(
                f"""
                <div style="
                    border:1px solid #30363d;
                    border-radius:14px;
                    padding:12px;
                    margin-bottom:10px;
                ">
                    <h4 style="margin:0;">{opinion['agent_name']}</h4>
                    <div style="font-size:26px; font-weight:700;">
                        {emoji(opinion['action'])} {opinion['action']}
                    </div>
                    <div>Confidence: {opinion['confidence']:.0%}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.subheader("Weighted Vote")

    vote_details = pd.DataFrame(result["weighted_vote"]["vote_details"])

    fig_votes = px.bar(
        vote_details,
        x="contribution",
        y="agent",
        color="action",
        orientation="h",
        text="action",
        title=None,
    )
    fig_votes.update_layout(height=250, margin=dict(l=5, r=5, t=5, b=5))
    st.plotly_chart(fig_votes, use_container_width=True)

    st.subheader("CIO Memo")

    if not cio.empty and ticker in cio["Ticker"].values:
        memo = cio[cio["Ticker"] == ticker].iloc[-1]
        st.success(f"{emoji(memo['Final_Decision'])} {memo['Final_Decision']}")
        st.write(f"Confidence: **{memo['Confidence']:.0%}**")
        with st.expander("Read memo"):
            st.write(memo["Investment_Memo"])
    else:
        st.info("No structured CIO memo yet.")

st.markdown("---")

bottom1, bottom2 = st.columns([0.5, 0.5])

with bottom1:
    st.subheader("Committee Debate")

    if result:
        st.info(result["debate"]["summary"])

        for point in result["debate"]["debate_points"]:
            with st.expander(f"{point['agent']} — {emoji(point['position'])} {point['position']}"):
                st.write(f"Confidence: **{point['confidence']:.0%}**")

                st.write("Bullish case")
                for item in point["bullish_case"] or ["None"]:
                    st.write(f"- {item}")

                st.write("Bearish case")
                for item in point["bearish_case"] or ["None"]:
                    st.write(f"- {item}")

                st.write("Risks")
                for item in point["risks"] or ["None"]:
                    st.write(f"- {item}")

st.subheader("Committee Memory Timeline")

if not memory.empty:
    ticker_memory = memory[memory["Ticker"] == ticker].sort_values("Timestamp")

    if not ticker_memory.empty:
        fig_memory = px.line(
            ticker_memory,
            x="Timestamp",
            y="Committee_Score",
            markers=True,
            title=f"{ticker} committee score over time",
        )

        fig_memory.update_layout(height=300, margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig_memory, use_container_width=True)

        recent_memory = ticker_memory.tail(5)[
            [
                "Timestamp",
                "Final_Action",
                "Committee_Score",
                "Buy_Votes",
                "Hold_Votes",
                "Sell_Votes",
                "Avg_Confidence",
            ]
        ]

        st.dataframe(recent_memory, use_container_width=True, height=180)
    else:
        st.info("No memory yet for this ticker.")
else:
    st.info("No committee memory file found yet.")

with bottom2:
    st.subheader("Latest Committee Summary")

    display = summary[
        [
            "Ticker",
            "Final_Action",
            "Committee_Score",
            "Buy_Votes",
            "Hold_Votes",
            "Sell_Votes",
            "Avg_Confidence",
            "Has_Disagreement",
        ]
    ].copy()

    st.dataframe(display, use_container_width=True, height=350)