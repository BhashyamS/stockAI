import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/ma_strategy_signals.csv")
OUTPUT_FILE = Path("data/processed/backtest_results.csv")

INITIAL_CASH = 10_000


def backtest_one_stock(df):
    df = df.sort_values("Date").copy()

    cash = INITIAL_CASH
    shares = 0
    portfolio_values = []

    for _, row in df.iterrows():
        price = row["Close"]
        signal = row["Signal"]

        if signal == "BUY" and shares == 0:
            shares = cash / price
            cash = 0

        elif signal == "SELL" and shares > 0:
            cash = shares * price
            shares = 0

        portfolio_value = cash + shares * price
        portfolio_values.append(portfolio_value)

    df["Portfolio_Value"] = portfolio_values
    df["Strategy_Return"] = df["Portfolio_Value"].pct_change()

    return df


def run_backtest():
    df = pd.read_csv(INPUT_FILE)
    df["Date"] = pd.to_datetime(df["Date"])

    results = []

    for ticker, group in df.groupby("Ticker"):
        print(f"Backtesting {ticker}...")
        result = backtest_one_stock(group)
        results.append(result)

        final_value = result["Portfolio_Value"].iloc[-1]
        total_return = (final_value / INITIAL_CASH - 1) * 100

        print(f"{ticker}: ${final_value:,.2f} | Return: {total_return:.2f}%")

    final_df = pd.concat(results, ignore_index=True)
    final_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved backtest results to {OUTPUT_FILE}")


if __name__ == "__main__":
    run_backtest()