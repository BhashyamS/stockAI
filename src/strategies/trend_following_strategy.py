import pandas as pd
from src.core.strategy import Strategy


class TrendFollowingStrategy(Strategy):
    name = "TrendFollowingV2"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["Signal"] = "HOLD"

        buy_condition = (
            (df["Close"] > df["MA_200"]) &
            (df["MA_50"] > df["MA_200"]) &
            (df["Momentum_10"] > 0) &
            (df["Volume_Ratio"] > 1)
        )

        sell_condition = (
            df["Close"] < df["MA_200"]
        )

        df.loc[buy_condition, "Signal"] = "BUY"
        df.loc[sell_condition, "Signal"] = "SELL"

        return df