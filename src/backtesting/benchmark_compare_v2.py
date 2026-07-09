import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/trend_v2_backtest_results.csv")
OUTPUT_FILE = Path("data/processed/trend_v2_benchmark_comparison.csv")

INITIAL_CASH = 10_000


def main():
    df = pd.read_csv(INPUT_FILE)

    rows = []

    for ticker, group in df.groupby("Ticker"):
        group = group.sort_values("Date")

        first_price = group["Close"].iloc[0]
        last_price = group["Close"].iloc[-1]

        strategy_final = group["Portfolio_Value"].iloc[-1]
        buy_hold_final = INITIAL_CASH * (last_price / first_price)

        rows.append({
            "Ticker": ticker,
            "Strategy_Final": strategy_final,
            "Buy_Hold_Final": buy_hold_final,
            "Strategy_Return_%": (strategy_final / INITIAL_CASH - 1) * 100,
            "Buy_Hold_Return_%": (buy_hold_final / INITIAL_CASH - 1) * 100,
            "Outperformance_%": ((strategy_final - buy_hold_final) / INITIAL_CASH) * 100
        })

    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT_FILE, index=False)

    print(result)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()