import pandas as pd
from pathlib import Path

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"

OUTPUT_FILE = Path("data/reference/ticker_universe.csv")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def clean_symbol(symbol):
    if pd.isna(symbol):
        return None

    symbol = str(symbol).strip().upper()

    if not symbol:
        return None

    # Skip test rows / metadata rows
    if symbol in ["FILE CREATION TIME"]:
        return None

    return symbol


def load_nasdaq_listed():
    df = pd.read_csv(NASDAQ_LISTED_URL, sep="|")
    df = df[df["Test Issue"] == "N"]

    out = pd.DataFrame({
        "Ticker": df["Symbol"].apply(clean_symbol),
        "Name": df["Security Name"],
        "Exchange": "NASDAQ",
        "ETF": df["ETF"],
    })

    return out


def load_other_listed():
    df = pd.read_csv(OTHER_LISTED_URL, sep="|")
    df = df[df["Test Issue"] == "N"]

    exchange_map = {
        "A": "NYSE American",
        "N": "NYSE",
        "P": "NYSE Arca",
        "Z": "BATS",
        "V": "IEX",
    }

    out = pd.DataFrame({
        "Ticker": df["ACT Symbol"].apply(clean_symbol),
        "Name": df["Security Name"],
        "Exchange": df["Exchange"].map(exchange_map).fillna(df["Exchange"]),
        "ETF": df["ETF"],
    })

    return out


def main():
    nasdaq = load_nasdaq_listed()
    other = load_other_listed()

    universe = pd.concat([nasdaq, other], ignore_index=True)
    universe = universe.dropna(subset=["Ticker"])
    universe = universe.drop_duplicates(subset=["Ticker"])
    universe = universe.sort_values("Ticker")

    universe.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved {len(universe)} tickers to {OUTPUT_FILE}")
    print(universe.head(20))


if __name__ == "__main__":
    main()