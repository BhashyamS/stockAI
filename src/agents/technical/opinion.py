from src.committee.schemas import AgentOpinion


class TechnicalOpinionAgent:
    agent_name = "Technical Agent"
    role = "Evaluates chart structure, trend, Heikin Ashi, RSI, momentum, and volatility."

    def run(self, row):
        score = 0
        bullish = []
        bearish = []
        neutral = []
        risks = []

        if row["HA_Color"] == "GREEN":
            score += 1
            bullish.append("Heikin Ashi candle is green")
        else:
            score -= 1
            bearish.append("Heikin Ashi candle is red")

        if row["Close"] > row["MA_200"]:
            score += 1
            bullish.append("Price is above MA200")
        else:
            score -= 1
            bearish.append("Price is below MA200")
            risks.append("Long-term trend may be weakening")

        if row["MA_50"] > row["MA_200"]:
            score += 1
            bullish.append("MA50 is above MA200")
        else:
            neutral.append("MA50 is not above MA200")

        if row["Momentum_10"] > 0:
            score += 1
            bullish.append("10-day momentum is positive")
        else:
            score -= 1
            bearish.append("10-day momentum is negative")

        if row["RSI_14"] > 75:
            score -= 1
            bearish.append("RSI is overbought")
            risks.append("Potential short-term pullback risk")

        if row["ATR_Ratio"] > 0.08:
            score -= 1
            bearish.append("ATR volatility is elevated")
            risks.append("High volatility may increase downside risk")

        if row["Drop_From_20D_High"] < -0.05:
            neutral.append("Stock is down more than 5% from 20-day high")

        if score >= 3:
            action = "BUY"
        elif score <= -2:
            action = "SELL"
        else:
            action = "HOLD"

        confidence = round(min(abs(score) / 6, 1), 2)

        return AgentOpinion(
            agent_name=self.agent_name,
            role=self.role,
            ticker=row["Ticker"],
            action=action,
            confidence=confidence,
            bullish_evidence=bullish,
            bearish_evidence=bearish,
            neutral_evidence=neutral,
            risks=risks,
            evidence={
                "close": row["Close"],
                "ha_color": row["HA_Color"],
                "rsi_14": row["RSI_14"],
                "ma_50": row["MA_50"],
                "ma_200": row["MA_200"],
                "momentum_10": row["Momentum_10"],
                "atr_ratio": row["ATR_Ratio"],
                "drop_from_20d_high": row["Drop_From_20D_High"],
            },
        )