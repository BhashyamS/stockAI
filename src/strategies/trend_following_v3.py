import pandas as pd
from src.core.strategy import Strategy


class TrendFollowingV3(Strategy):
    name = "TrendFollowingV3"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["Signal"] = "HOLD"

        buy_condition = (
            (df["Close"] > df["MA_200"]) &
            (df["MA_50"] > df["MA_200"]) &
            (df["Momentum_10"] > -0.02)
        )

        sell_condition = (
            (df["Close"] < df["MA_200"] * 0.95)
        )

        df.loc[buy_condition, "Signal"] = "BUY"
        df.loc[sell_condition, "Signal"] = "SELL"

        return df