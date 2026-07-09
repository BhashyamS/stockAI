import pandas as pd
import numpy as np


class BacktestEngine:
    def __init__(
        self,
        initial_cash=10_000,
        transaction_cost=0.001,
        slippage=0.001
    ):
        self.initial_cash = initial_cash
        self.transaction_cost = transaction_cost
        self.slippage = slippage

    def run_one_stock(self, df: pd.DataFrame):
        df = df.sort_values("Date").copy().reset_index(drop=True)

        cash = self.initial_cash
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
                buy_price = execution_price * (1 + self.slippage)
                shares = (cash * (1 - self.transaction_cost)) / buy_price
                cash = 0
                position = True
                entry_price = buy_price
                entry_date = tomorrow["Date"]

            elif signal == "SELL" and position:
                sell_price = execution_price * (1 - self.slippage)
                cash = shares * sell_price * (1 - self.transaction_cost)

                trades.append({
                    "Ticker": today["Ticker"],
                    "Entry_Date": entry_date,
                    "Exit_Date": tomorrow["Date"],
                    "Entry_Price": entry_price,
                    "Exit_Price": sell_price,
                    "Trade_Return": (sell_price - entry_price) / entry_price,
                    "Profit": cash - self.initial_cash
                })

                shares = 0
                position = False

            portfolio_value = cash + shares * today["Close"]
            portfolio_values.append(portfolio_value)

        result = df.iloc[:-1].copy()
        result["Portfolio_Value"] = portfolio_values
        result["Strategy_Return"] = result["Portfolio_Value"].pct_change()

        return result, trades

    def calculate_metrics(self, result: pd.DataFrame):
        final_value = result["Portfolio_Value"].iloc[-1]
        total_return = final_value / self.initial_cash - 1

        daily_returns = result["Strategy_Return"].dropna()
        sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std()

        rolling_max = result["Portfolio_Value"].cummax()
        drawdown = result["Portfolio_Value"] / rolling_max - 1
        max_drawdown = drawdown.min()

        years = len(result) / 252
        cagr = (final_value / self.initial_cash) ** (1 / years) - 1

        return {
            "Final_Value": final_value,
            "Total_Return_%": total_return * 100,
            "CAGR_%": cagr * 100,
            "Sharpe_Ratio": sharpe,
            "Max_Drawdown_%": max_drawdown * 100
        }