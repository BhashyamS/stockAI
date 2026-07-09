import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/pro_backtest_results.csv")
OUTPUT_FILE = Path("data/processed/benchmark_comparison.csv")

INITIAL_CASH = 10_000


def compare_benchmark():
    df = pd.read_csv(INPUT_FILE)
    results = []

    for ticker, group in df.groupby("Ticker"):
        group = group.sort_values("Date").copy()

        first_price = group["Close"].iloc[0]
        last_price = group["Close"].iloc[-1]

        buy_hold_final = INITIAL_CASH * (last_price / first_price)
        strategy_final = group["Portfolio_Value"].iloc[-1]

        results.append({
            "Ticker": ticker,
            "Strategy_Final": strategy_final,
            "Buy_Hold_Final": buy_hold_final,
            "Strategy_Return_%": (strategy_final / INITIAL_CASH - 1) * 100,
            "Buy_Hold_Return_%": (buy_hold_final / INITIAL_CASH - 1) * 100,
            "Outperformance_%": ((strategy_final - buy_hold_final) / INITIAL_CASH) * 100
        })

    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT_FILE, index=False)

    print(result_df)
    print(f"\nSaved benchmark comparison to {OUTPUT_FILE}")


if __name__ == "__main__":
    compare_benchmark()