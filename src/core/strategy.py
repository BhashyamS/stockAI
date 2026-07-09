from abc import ABC, abstractmethod
import pandas as pd


class Strategy(ABC):
    name = "BaseStrategy"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        pass