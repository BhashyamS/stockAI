import streamlit as st
import pandas as pd
from pathlib import Path

DATA_FILE = Path("data/processed/agent_recommendations.csv")

st.set_page_config(page_title="StockAI Agent", layout="wide")

st.title("StockAI Agent")
st.caption("AI-assisted market analysis and trade recommendation dashboard")

df = pd.read_csv(DATA_FILE)
df["Date"] = pd.to_datetime(df["Date"])

latest = df.sort_values("Date").groupby("Ticker").tail(1)

ticker = st.selectbox("Select ticker", latest["Ticker"].unique())

row = latest[latest["Ticker"] == ticker].iloc[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Action", row["Agent_Action"])
col2.metric("Confidence", f"{row['Agent_Confidence']:.0%}")
col3.metric("Suggested Position", f"{row['Suggested_Position_%']}%")
col4.metric("ML 5D Up Probability", f"{row['ML_Prob_5D_Up']:.0%}")

st.subheader("Agent Explanation")
st.write(row["Agent_Explanation"])

st.subheader("Latest Recommendations")
st.dataframe(
    latest[[
        "Date",
        "Ticker",
        "Close",
        "ML_Prob_5D_Up",
        "Agent_Action",
        "Agent_Confidence",
        "Suggested_Position_%"
    ]],
    use_container_width=True
)