import argparse
import pandas as pd
from pathlib import Path

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.trend_following_strategy import TrendFollowingStrategy
from src.strategies.trend_following_v3 import TrendFollowingV3
from src.strategies.risk_aware_trend_v4 import RiskAwareTrendV4

INPUT_FILE = Path("data/processed/features_clean.csv")

STRATEGIES = {
    "v2": TrendFollowingStrategy,
    "v3": TrendFollowingV3,
    "v4": RiskAwareTrendV4,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strategy",
        choices=STRATEGIES.keys(),
        default="v3",
        help="Choose which strategy to run"
    )
    args = parser.parse_args()

    df = pd.read_csv(INPUT_FILE)
    df["Date"] = pd.to_datetime(df["Date"])

    strategy = STRATEGIES[args.strategy]()
    engine = BacktestEngine()

    results_file = Path(f"data/processed/{strategy.name}_backtest_results.csv")
    trades_file = Path(f"data/processed/{strategy.name}_trade_log.csv")
    metrics_file = Path(f"data/processed/{strategy.name}_metrics.csv")

    all_results = []
    all_trades = []
    all_metrics = []

    for ticker, group in df.groupby("Ticker"):
        print(f"Running {strategy.name} on {ticker}...")

        signal_df = strategy.generate_signals(group)
        result, trades = engine.run_one_stock(signal_df)

        metrics = engine.calculate_metrics(result)
        metrics["Ticker"] = ticker
        metrics["Strategy"] = strategy.name

        all_results.append(result)
        all_trades.extend(trades)
        all_metrics.append(metrics)

        print(
            f"{ticker}: ${metrics['Final_Value']:,.2f} | "
            f"Return: {metrics['Total_Return_%']:.2f}% | "
            f"Sharpe: {metrics['Sharpe_Ratio']:.2f} | "
            f"Max DD: {metrics['Max_Drawdown_%']:.2f}%"
        )

    pd.concat(all_results).to_csv(results_file, index=False)
    pd.DataFrame(all_trades).to_csv(trades_file, index=False)
    pd.DataFrame(all_metrics).to_csv(metrics_file, index=False)

    print("\nSaved:")
    print(results_file)
    print(trades_file)
    print(metrics_file)


if __name__ == "__main__":
    main()