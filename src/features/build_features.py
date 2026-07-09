import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/all_prices.csv")
OUTPUT_FILE = Path("data/processed/features.csv")


def add_features(group):
    group = group.sort_values("Date").copy()

    group["Daily_Return"] = group["Close"].pct_change()

    group["MA_5"] = group["Close"].rolling(5).mean()
    group["MA_20"] = group["Close"].rolling(20).mean()
    group["MA_50"] = group["Close"].rolling(50).mean()
    group["MA_200"] = group["Close"].rolling(200).mean()

    group["Volatility_20"] = group["Daily_Return"].rolling(20).std()
    group["Momentum_10"] = group["Close"] / group["Close"].shift(10) - 1

    group["Volume_MA_20"] = group["Volume"].rolling(20).mean()
    group["Volume_Ratio"] = group["Volume"] / group["Volume_MA_20"]

    delta = group["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    group["RSI_14"] = 100 - (100 / (1 + rs))

    group["Target_Next_Day_Up"] = (
        group["Close"].shift(-1) > group["Close"]
    ).astype(int)

    high_low = group["High"] - group["Low"]
    high_close = (group["High"] - group["Close"].shift(1)).abs()
    low_close = (group["Low"] - group["Close"].shift(1)).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

    group["ATR_14"] = true_range.rolling(14).mean()
    group["ATR_Ratio"] = group["ATR_14"] / group["Close"]

    group["Future_5D_Return"] = group["Close"].shift(-5) / group["Close"] - 1
    group["Target_5D_Up"] = (group["Future_5D_Return"] > 0).astype(int)

    group["HA_Close"] = (
        group["Open"] + group["High"] + group["Low"] + group["Close"]
    ) / 4

    ha_open = []

    for i in range(len(group)):
        if i == 0:
            ha_open.append((group["Open"].iloc[i] + group["Close"].iloc[i]) / 2)
        else:
            ha_open.append((ha_open[i - 1] + group["HA_Close"].iloc[i - 1]) / 2)

    group["HA_Open"] = ha_open
    group["HA_High"] = group[["High", "HA_Open", "HA_Close"]].max(axis=1)
    group["HA_Low"] = group[["Low", "HA_Open", "HA_Close"]].min(axis=1)

    group["HA_Color"] = group.apply(
        lambda row: "GREEN" if row["HA_Close"] >= row["HA_Open"] else "RED",
        axis=1
    )

    group["HA_Body"] = (group["HA_Close"] - group["HA_Open"]).abs()
    group["HA_Range"] = group["HA_High"] - group["HA_Low"]
    group["HA_Body_Ratio"] = group["HA_Body"] / group["HA_Range"]

    group["Drop_From_20D_High"] = group["Close"] / group["Close"].rolling(20).max() - 1
        
    return group


def build_features():
    df = pd.read_csv(INPUT_FILE)
    df["Date"] = pd.to_datetime(df["Date"])

    featured_groups = []

    for ticker in df["Ticker"].unique():
        ticker_df = df[df["Ticker"] == ticker].copy()
        ticker_features = add_features(ticker_df)
        featured_groups.append(ticker_features)

    featured_df = pd.concat(featured_groups, ignore_index=True)

    featured_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved features to {OUTPUT_FILE}")
    print(featured_df.head())
    print(featured_df.columns)


if __name__ == "__main__":
    build_features()