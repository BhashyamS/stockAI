import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/features_clean.csv")
OUTPUT_FILE = Path("data/processed/ma_strategy_signals.csv")


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Signal"] = "HOLD"

    buy_condition = (
        (df["Close"] > df["MA_50"]) &
        (df["MA_50"] > df["MA_200"]) &
        (df["RSI_14"] < 70) &
        (df["Momentum_10"] > 0)
    )

    sell_condition = (
        (df["Close"] < df["MA_50"]) |
        (df["RSI_14"] > 75) |
        (df["Momentum_10"] < -0.05)
    )

    df.loc[buy_condition, "Signal"] = "BUY"
    df.loc[sell_condition, "Signal"] = "SELL"

    return df


def main():
    df = pd.read_csv(INPUT_FILE)
    signals_df = generate_signals(df)

    signals_df.to_csv(OUTPUT_FILE, index=False)

    print(signals_df["Signal"].value_counts())
    print(f"Saved signals to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()