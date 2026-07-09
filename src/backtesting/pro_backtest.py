import pandas as pd
import numpy as np
from pathlib import Path

INPUT_FILE = Path("data/processed/ma_strategy_signals.csv")
RESULTS_FILE = Path("data/processed/pro_backtest_results.csv")
TRADES_FILE = Path("data/processed/trade_log.csv")

INITIAL_CASH = 10_000
TRANSACTION_COST = 0.001  # 0.1%
SLIPPAGE = 0.001          # 0.1%


def backtest_one_stock(df):
    df = df.sort_values("Date").copy().reset_index(drop=True)

    cash = INITIAL_CASH
    shares = 0
    position = False
    entry_price = 0
    entry_date = None

    portfolio_values = []
    trades = []

    for i in range(len(df) - 1):
        today = df.iloc[i]
        tomorrow = df.iloc[i + 1]

        signal = today["Signal"]
        execution_price = tomorrow["Open"]

        if signal == "BUY" and not position:
            buy_price = execution_price * (1 + SLIPPAGE)
            shares = (cash * (1 - TRANSACTION_COST)) / buy_price
            cash = 0
            position = True
            entry_price = buy_price
            entry_date = tomorrow["Date"]

        elif signal == "SELL" and position:
            sell_price = execution_price * (1 - SLIPPAGE)
            cash = shares * sell_price * (1 - TRANSACTION_COST)

            trade_return = (sell_price - entry_price) / entry_price

            trades.append({
                "Ticker": today["Ticker"],
                "Entry_Date": entry_date,
                "Exit_Date": tomorrow["Date"],
                "Entry_Price": entry_price,
                "Exit_Price": sell_price,
                "Trade_Return": trade_return,
                "Profit": cash - INITIAL_CASH
            })

            shares = 0
            position = False

        current_price = today["Close"]
        portfolio_value = cash + shares * current_price
        portfolio_values.append(portfolio_value)

    df = df.iloc[:-1].copy()
    df["Portfolio_Value"] = portfolio_values
    df["Strategy_Return"] = df["Portfolio_Value"].pct_change()

    return df, trades


def calculate_metrics(result):
    final_value = result["Portfolio_Value"].iloc[-1]
    total_return = final_value / INITIAL_CASH - 1

    daily_returns = result["Strategy_Return"].dropna()
    sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std()

    rolling_max = result["Portfolio_Value"].cummax()
    drawdown = result["Portfolio_Value"] / rolling_max - 1
    max_drawdown = drawdown.min()

    years = len(result) / 252
    cagr = (final_value / INITIAL_CASH) ** (1 / years) - 1

    return {
        "Final_Value": final_value,
        "Total_Return_%": total_return * 100,
        "CAGR_%": cagr * 100,
        "Sharpe_Ratio": sharpe,
        "Max_Drawdown_%": max_drawdown * 100
    }


def run_backtest():
    df = pd.read_csv(INPUT_FILE)
    df["Date"] = pd.to_datetime(df["Date"])

    all_results = []
    all_trades = []
    metrics = []

    for ticker, group in df.groupby("Ticker"):
        print(f"Backtesting {ticker}...")

        result, trades = backtest_one_stock(group)
        all_results.append(result)
        all_trades.extend(trades)

        ticker_metrics = calculate_metrics(result)
        ticker_metrics["Ticker"] = ticker
        metrics.append(ticker_metrics)

        print(
            f"{ticker}: ${ticker_metrics['Final_Value']:,.2f} | "
            f"Return: {ticker_metrics['Total_Return_%']:.2f}% | "
            f"Sharpe: {ticker_metrics['Sharpe_Ratio']:.2f} | "
            f"Max DD: {ticker_metrics['Max_Drawdown_%']:.2f}%"
        )

    results_df = pd.concat(all_results, ignore_index=True)
    trades_df = pd.DataFrame(all_trades)
    metrics_df = pd.DataFrame(metrics)

    results_df.to_csv(RESULTS_FILE, index=False)
    trades_df.to_csv(TRADES_FILE, index=False)

    print("\nSummary:")
    print(metrics_df)

    print(f"\nSaved results to {RESULTS_FILE}")
    print(f"Saved trade log to {TRADES_FILE}")


if __name__ == "__main__":
    run_backtest()