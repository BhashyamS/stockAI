import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="AI Investment Committee", layout="wide")

DATA_FILE = Path("data/processed/investment_committee_report.csv")
FEATURES_FILE = Path("data/processed/features_clean.csv")
CIO_FILE = Path("data/processed/cio_gemini_memos.csv")


@st.cache_data
def load_data():
    committee_df = pd.read_csv(DATA_FILE)
    committee_df["Date"] = pd.to_datetime(committee_df["Date"])

    features_df = pd.read_csv(FEATURES_FILE)
    features_df["Date"] = pd.to_datetime(features_df["Date"])

    if CIO_FILE.exists():
        cio_df = pd.read_csv(CIO_FILE)
    else:
        cio_df = pd.DataFrame()

    return committee_df, features_df, cio_df


def parse_json_list(value):
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    return [str(value)]


def decision_emoji(decision):
    if decision == "BUY":
        return "🟢"
    if decision == "SELL":
        return "🔴"
    return "🟡"


def decision_label(decision):
    return f"{decision_emoji(decision)} {decision}"


def build_price_chart(ticker, features_df, committee_df, selected_range):
    price_df = features_df[features_df["Ticker"] == ticker].copy()
    price_df = price_df.sort_values("Date")

    signal_df = committee_df[committee_df["Ticker"] == ticker].copy()
    signal_df["Date"] = pd.to_datetime(signal_df["Date"])

    chart_df = price_df.merge(
        signal_df[
            [
                "Date",
                "Ticker",
                "Final_Decision",
                "Final_Confidence",
                "Committee_Summary",
            ]
        ],
        on=["Date", "Ticker"],
        how="left",
    )

    max_date = chart_df["Date"].max()

    if selected_range == "1M":
        start_date = max_date - pd.DateOffset(months=1)
    elif selected_range == "3M":
        start_date = max_date - pd.DateOffset(months=3)
    elif selected_range == "6M":
        start_date = max_date - pd.DateOffset(months=6)
    elif selected_range == "1Y":
        start_date = max_date - pd.DateOffset(years=1)
    elif selected_range == "3Y":
        start_date = max_date - pd.DateOffset(years=3)
    elif selected_range == "5Y":
        start_date = max_date - pd.DateOffset(years=5)
    else:
        start_date = chart_df["Date"].min()

    chart_df = chart_df[chart_df["Date"] >= start_date].copy()

    chart_df["Signal_Text"] = chart_df["Final_Decision"].fillna("No signal")
    chart_df["Confidence_Text"] = chart_df["Final_Confidence"].fillna(0)
    chart_df["Summary_Text"] = chart_df["Committee_Summary"].fillna(
        "No committee signal for this date."
    )

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=chart_df["Date"],
            open=chart_df["Open"],
            high=chart_df["High"],
            low=chart_df["Low"],
            close=chart_df["Close"],
            name="Price",
            customdata=chart_df[
                [
                    "Signal_Text",
                    "Confidence_Text",
                    "Summary_Text",
                    "HA_Color",
                    "RSI_14",
                ]
            ],
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Open: $%{open:.2f}<br>"
                "High: $%{high:.2f}<br>"
                "Low: $%{low:.2f}<br>"
                "Close: $%{close:.2f}<br><br>"
                "Signal: %{customdata[0]}<br>"
                "Confidence: %{customdata[1]:.0%}<br>"
                "Heikin Ashi: %{customdata[3]}<br>"
                "RSI: %{customdata[4]:.1f}<br><br>"
                "%{customdata[2]}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["Date"],
            y=chart_df["MA_50"],
            mode="lines",
            name="MA 50",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["Date"],
            y=chart_df["MA_200"],
            mode="lines",
            name="MA 200",
        )
    )

    buy_points = chart_df[chart_df["Final_Decision"] == "BUY"]
    sell_points = chart_df[chart_df["Final_Decision"] == "SELL"]
    hold_points = chart_df[chart_df["Final_Decision"] == "HOLD"]

    fig.add_trace(
        go.Scatter(
            x=buy_points["Date"],
            y=buy_points["Close"],
            mode="markers",
            name="BUY",
            marker=dict(size=14, symbol="triangle-up"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=sell_points["Date"],
            y=sell_points["Close"],
            mode="markers",
            name="SELL",
            marker=dict(size=14, symbol="triangle-down"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hold_points["Date"],
            y=hold_points["Close"],
            mode="markers",
            name="HOLD",
            marker=dict(size=8, symbol="circle"),
        )
    )

    fig.update_layout(
        height=520,
        margin=dict(l=5, r=5, t=40, b=5),
        xaxis_rangeslider_visible=True,
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(count=3, label="3Y", step="year", stepmode="backward"),
                        dict(step="all", label="All"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        ),
        yaxis_title="Price",
        title=f"{ticker} price trend",
    )

    return fig


df, features_df, cio_df = load_data()

latest_features = features_df.sort_values("Date").groupby("Ticker").tail(1)

overview_df = df.merge(
    latest_features[
        [
            "Ticker",
            "Daily_Return",
            "Momentum_10",
            "Drop_From_20D_High",
            "ATR_Ratio",
            "RSI_14",
            "HA_Color",
        ]
    ],
    on="Ticker",
    how="left",
)

overview_df["Decision_Score"] = overview_df["Final_Decision"].map(
    {"BUY": 1, "HOLD": 0, "SELL": -1}
)

st.title("AI Investment Committee")
st.caption("Visual multi-agent stock research dashboard")

# Ticker selector as dashboard cards, not sidebar
st.subheader("Portfolio Watchlist")

ticker_cols = st.columns(len(df))

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = df["Ticker"].iloc[0]

for i, (_, ticker_row) in enumerate(df.sort_values("Ticker").iterrows()):
    with ticker_cols[i]:
        is_selected = st.session_state.selected_ticker == ticker_row["Ticker"]

        label = (
            f"{ticker_row['Ticker']}\n"
            f"{decision_emoji(ticker_row['Final_Decision'])} "
            f"{ticker_row['Final_Decision']}\n"
            f"{ticker_row['Final_Confidence']:.0%}"
        )

        if st.button(label, key=f"ticker_{ticker_row['Ticker']}", use_container_width=True):
            st.session_state.selected_ticker = ticker_row["Ticker"]

ticker = st.session_state.selected_ticker
row = df[df["Ticker"] == ticker].iloc[0]

range_cols = st.columns([0.55, 0.45])
with range_cols[0]:
    st.markdown(f"### Selected: `{ticker}`")
with range_cols[1]:
    selected_range = st.radio(
        "Chart range",
        ["1M", "3M", "6M", "1Y", "3Y", "5Y", "All"],
        index=3,
        horizontal=True,
    )

st.markdown("---")

# Single dashboard layout
left, right = st.columns([0.68, 0.32])

with left:
    st.plotly_chart(
        build_price_chart(ticker, features_df, df, selected_range),
        width="stretch",
    )

    st.subheader("Portfolio Heatmap")

    heatmap_df = overview_df.set_index("Ticker")[
        [
            "Decision_Score",
            "Final_Confidence",
            "ML_Prob_5D_Up",
            "ATR_Ratio",
            "Momentum_10",
            "Drop_From_20D_High",
            "RSI_14",
        ]
    ]

    fig_heatmap = px.imshow(
        heatmap_df,
        text_auto=".2f",
        aspect="auto",
        title="Signals, risk, momentum, and model probability",
    )

    fig_heatmap.update_layout(height=320, margin=dict(l=5, r=5, t=45, b=5))
    st.plotly_chart(fig_heatmap, width="stretch")

with right:
    st.subheader("Current Decision")

    st.markdown(
        f"""
        <div style="
            border:1px solid #30363d;
            border-radius:16px;
            padding:18px;
            margin-bottom:14px;
        ">
            <h2 style="margin-bottom:0;">{decision_label(row["Final_Decision"])}</h2>
            <p style="font-size:14px; opacity:0.75;">{ticker} committee recommendation</p>
            <h3>{row["Final_Confidence"]:.0%} confidence</h3>
            <p><b>Position:</b> {row["Position_Size_%"]}%</p>
            <p><b>Risk:</b> {row["Risk_Level"]}</p>
            <p><b>ML 5D Up:</b> {row["ML_Prob_5D_Up"]:.0%}</p>
            <p><b>Price:</b> ${row["Close"]:.2f}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Agent Votes")

    votes = pd.DataFrame(
        {
            "Agent": ["Technical", "ML", "Risk", "Executive"],
            "Action": [
                row["Technical_Action"],
                row["ML_Action"],
                row["Risk_Action"],
                row["Executive_Action"],
            ],
            "Confidence": [
                row["Technical_Confidence"],
                row["ML_Confidence"],
                row["Risk_Confidence"],
                row["Executive_Confidence"],
            ],
        }
    )

    fig_votes = px.bar(
        votes,
        x="Confidence",
        y="Agent",
        color="Action",
        text="Action",
        orientation="h",
        title=None,
    )
    fig_votes.update_xaxes(range=[0, 1])
    fig_votes.update_layout(height=260, margin=dict(l=5, r=5, t=10, b=5))
    st.plotly_chart(fig_votes, width="stretch")

    st.subheader("CIO Memo")

    memo_row = pd.DataFrame()
    if not cio_df.empty:
        memo_row = cio_df[cio_df["Ticker"] == ticker]

    if not memo_row.empty:
        memo = memo_row.iloc[-1]

        st.markdown(
            f"""
            <div style="
                border:1px solid #30363d;
                border-radius:16px;
                padding:14px;
                margin-bottom:10px;
            ">
                <b>CIO:</b> {decision_label(memo["Final_Decision"])}<br>
                <b>Confidence:</b> {memo["Confidence"]:.0%}<br>
                <b>Position:</b> {memo["Position_Size_%"]}%
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Read memo"):
            st.write(memo["Investment_Memo"])

        with st.expander("Key reasons"):
            for item in parse_json_list(memo["Key_Reasons"]):
                st.write(f"- {item}")

        with st.expander("Risks"):
            for item in parse_json_list(memo["Main_Risks"]):
                st.write(f"- {item}")

        with st.expander("What would change the decision"):
            for item in parse_json_list(memo["What_Would_Change_Decision"]):
                st.write(f"- {item}")
    else:
        st.warning("No CIO memo for this ticker.")

st.markdown("---")

bottom_left, bottom_right = st.columns([0.5, 0.5])

with bottom_left:
    st.subheader("Latest Decisions")

    compact = df[
        [
            "Ticker",
            "Close",
            "Final_Decision",
            "Final_Confidence",
            "Risk_Level",
            "ML_Prob_5D_Up",
        ]
    ].copy()

    compact["Close"] = compact["Close"].round(2)
    compact["Final_Confidence"] = (compact["Final_Confidence"] * 100).round(0)
    compact["ML_Prob_5D_Up"] = (compact["ML_Prob_5D_Up"] * 100).round(0)

    st.dataframe(compact, width="stretch", height=280)

with bottom_right:
    st.subheader("Decision Breakdown")

    summary = df["Final_Decision"].value_counts().reset_index()
    summary.columns = ["Decision", "Count"]

    fig_summary = px.pie(
        summary,
        names="Decision",
        values="Count",
        title=None,
    )
    fig_summary.update_layout(height=280, margin=dict(l=5, r=5, t=5, b=5))
    st.plotly_chart(fig_summary, width="stretch")

with st.expander("Committee reasoning details"):
    st.write("**Committee Summary**")
    st.info(row["Committee_Summary"])

    st.write("**Technical Agent**")
    st.write(row["Technical_View"])

    st.write("**ML Agent**")
    st.write(row["ML_View"])

    st.write("**Risk Agent**")
    st.write(row["Risk_View"])

    st.write("**Executive Agent**")
    st.write(row["Executive_Explanation"])

with st.expander("Full investment memo"):
    st.text(row["Full_Investment_Memo"])