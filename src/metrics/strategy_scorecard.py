import argparse
import pandas as pd
import numpy as np
from pathlib import Path

INITIAL_CASH = 10_000


def calculate_metrics(group, value_col, return_col=None):
    final_value = group[value_col].iloc[-1]
    total_return = final_value / INITIAL_CASH - 1

    if return_col:
        daily_returns = group[return_col].dropna()
    else:
        daily_returns = group[value_col].pct_change().dropna()

    sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std()

    rolling_max = group[value_col].cummax()
    drawdown = group[value_col] / rolling_max - 1
    max_dd = drawdown.min()

    years = len(group) / 252
    cagr = (final_value / INITIAL_CASH) ** (1 / years) - 1

    return final_value, total_return, cagr, sharpe, max_dd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    args = parser.parse_args()

    input_file = Path(f"data/processed/{args.strategy}_backtest_results.csv")
    output_file = Path(f"data/processed/{args.strategy}_scorecard.csv")

    df = pd.read_csv(input_file)
    df["Date"] = pd.to_datetime(df["Date"])

    rows = []

    for ticker, group in df.groupby("Ticker"):
        group = group.sort_values("Date").copy()

        first_price = group["Close"].iloc[0]
        group["BuyHold_Value"] = INITIAL_CASH * (group["Close"] / first_price)

        strategy = calculate_metrics(group, "Portfolio_Value", "Strategy_Return")
        buy_hold = calculate_metrics(group, "BuyHold_Value")

        rows.append({
            "Ticker": ticker,
            "Strategy_Final": strategy[0],
            "BuyHold_Final": buy_hold[0],
            "Strategy_Return_%": strategy[1] * 100,
            "BuyHold_Return_%": buy_hold[1] * 100,
            "Strategy_CAGR_%": strategy[2] * 100,
            "BuyHold_CAGR_%": buy_hold[2] * 100,
            "Strategy_Sharpe": strategy[3],
            "BuyHold_Sharpe": buy_hold[3],
            "Strategy_MaxDD_%": strategy[4] * 100,
            "BuyHold_MaxDD_%": buy_hold[4] * 100,
            "Return_Outperformance_%": (strategy[1] - buy_hold[1]) * 100,
            "Sharpe_Outperformance": strategy[3] - buy_hold[3],
            "Drawdown_Improvement_%": (buy_hold[4] - strategy[4]) * 100,
        })

    scorecard = pd.DataFrame(rows)
    scorecard.to_csv(output_file, index=False)

    print(scorecard)
    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()