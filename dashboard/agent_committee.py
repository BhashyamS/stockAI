import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="AI Investment Committee", layout="wide")

st.title("AI Investment Committee")
st.caption("Technical Agent + ML Agent + Risk Agent → Executive Portfolio Decision")

DATA_FILE = Path("data/processed/executive_agent_recommendations.csv")

df = pd.read_csv(DATA_FILE)
df["Date"] = pd.to_datetime(df["Date"])

latest = df.sort_values("Date").groupby("Ticker").tail(1)

ticker = st.selectbox("Select ticker", sorted(latest["Ticker"].unique()))

row = latest[latest["Ticker"] == ticker].iloc[0]

st.header(f"{ticker} Recommendation")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Final Action", row["Executive_Action"])
col2.metric("Executive Confidence", f"{row['Executive_Confidence']:.0%}")
col3.metric("Suggested Position", f"{row['Suggested_Position_%']}%")
col4.metric("ML 5-Day Up Probability", f"{row['ML_Prob_5D_Up']:.0%}")

st.markdown("---")

st.subheader("Agent Votes")

votes = pd.DataFrame({
    "Agent": ["Technical Agent", "ML Agent", "Risk Agent", "Executive Agent"],
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
    "Reason": [
        row["Technical_Reason"],
        row["ML_Reason"],
        row["Risk_Reason"],
        row["Executive_Explanation"],
    ],
})

st.dataframe(votes, use_container_width=True)

fig_votes = px.bar(
    votes,
    x="Agent",
    y="Confidence",
    color="Action",
    text="Action",
    title=f"{ticker}: Agent confidence by vote",
)

fig_votes.update_yaxes(range=[0, 1])
st.plotly_chart(fig_votes, use_container_width=True)

st.subheader("Committee Explanation")

st.info(row["Executive_Explanation"])

st.markdown("---")

st.subheader("All Latest Recommendations")

st.dataframe(
    latest[
        [
            "Date",
            "Ticker",
            "Close",
            "Technical_Action",
            "ML_Action",
            "Risk_Action",
            "Risk_Level",
            "Executive_Action",
            "Executive_Confidence",
            "Suggested_Position_%",
        ]
    ],
    use_container_width=True,
)

summary = latest["Executive_Action"].value_counts().reset_index()
summary.columns = ["Action", "Count"]

fig_summary = px.pie(
    summary,
    names="Action",
    values="Count",
    title="Final recommendation breakdown",
)

st.plotly_chart(fig_summary, use_container_width=True)