import pandas as pd
from pathlib import Path

RAW_FOLDER = Path("data/raw")
PROCESSED_FOLDER = Path("data/processed")
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = PROCESSED_FOLDER / "all_prices.csv"


def combine_csv_files():
    all_data = []

    for file in RAW_FOLDER.glob("*.csv"):
        print(f"Reading {file.name}...")

        df = pd.read_csv(file)

        # Remove weird extra header rows if they exist
        df = df[df["Date"] != "Ticker"]
        df = df.dropna(subset=["Date", "Ticker"])

        all_data.append(df)

    combined_df = pd.concat(all_data, ignore_index=True)

    combined_df["Date"] = pd.to_datetime(combined_df["Date"])

    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    combined_df[numeric_cols] = combined_df[numeric_cols].apply(pd.to_numeric)

    combined_df = combined_df.sort_values(["Ticker", "Date"])

    combined_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Combined dataset saved to {OUTPUT_FILE}")
    print(combined_df.head())
    print(combined_df.shape)


if __name__ == "__main__":
    combine_csv_files()