import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Watchlist Manager", layout="wide")

UNIVERSE_FILE = Path("data/reference/ticker_universe.csv")
WATCHLIST_FILE = Path("config/watchlist.txt")
WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)

st.title("Watchlist Manager")
st.caption("Search the full ticker universe and choose which stocks the AI committee should analyze.")

universe = pd.read_csv(UNIVERSE_FILE)

if WATCHLIST_FILE.exists():
    current_watchlist = [
        line.strip().upper()
        for line in WATCHLIST_FILE.read_text().splitlines()
        if line.strip()
    ]
else:
    current_watchlist = []

search = st.text_input("Search ticker or company name", placeholder="Example: Apple, NVDA, Tesla, VOO")

filtered = universe.copy()

if search:
    s = search.upper()
    filtered = universe[
        universe["Ticker"].astype(str).str.contains(s, na=False)
        | universe["Name"].astype(str).str.upper().str.contains(s, na=False)
    ]

st.subheader("Search Results")

selected = st.multiselect(
    "Select tickers to add",
    options=filtered["Ticker"].head(100).tolist(),
    format_func=lambda t: f"{t} — {filtered[filtered['Ticker'] == t]['Name'].iloc[0]}",
)

if st.button("Add to Watchlist"):
    updated = sorted(set(current_watchlist + selected))
    WATCHLIST_FILE.write_text("\n".join(updated))
    st.success("Watchlist updated.")
    st.rerun()

st.subheader("Current Watchlist")

st.write(current_watchlist)

remove = st.multiselect("Remove tickers", current_watchlist)

if st.button("Remove Selected"):
    updated = [t for t in current_watchlist if t not in remove]
    WATCHLIST_FILE.write_text("\n".join(updated))
    st.success("Removed selected tickers.")
    st.rerun()

st.markdown("---")

st.info("After changing the watchlist, rerun the data pipeline so the AI committee can analyze the new tickers.")