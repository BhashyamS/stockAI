import pandas as pd
from pathlib import Path

RAW_FOLDER = Path("data/raw")
PROCESSED_FOLDER = Path("data/processed")
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = PROCESSED_FOLDER / "all_prices.csv"


def combine_csv_files():
    all_data = []

    for file in RAW_FOLDER.glob("*.csv"):
        ticker = file.stem
        print(f"Reading {file.name} as {ticker}...")

        df = pd.read_csv(file)

        # Remove bad yfinance extra rows
        df = df[pd.to_datetime(df["Date"], errors="coerce").notna()]

        df["Date"] = pd.to_datetime(df["Date"])
        df["Ticker"] = ticker

        numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

        df = df.dropna(subset=numeric_cols)

        all_data.append(df)

    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df = combined_df.sort_values(["Ticker", "Date"])

    combined_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved to {OUTPUT_FILE}")
    print(combined_df.head())
    print(combined_df.columns)


if __name__ == "__main__":
    combine_csv_files()