import yfinance as yf
import pandas as pd
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------
TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "SPY"
]

START_DATE = "2015-01-01"

RAW_FOLDER = Path("data/raw")
RAW_FOLDER.mkdir(parents=True, exist_ok=True)


def download_stock(ticker: str):

    print(f"Downloading {ticker}...")

    df = yf.download(
        ticker,
        start=START_DATE,
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        print(f"No data found for {ticker}")
        return

    df.reset_index(inplace=True)

    df["Ticker"] = ticker

    save_path = RAW_FOLDER / f"{ticker}.csv"

    df.to_csv(save_path, index=False)

    print(f"Saved -> {save_path}")
    print(df.head())
    print("-" * 60)


def main():

    for ticker in TICKERS:
        download_stock(ticker)


if __name__ == "__main__":
    main()