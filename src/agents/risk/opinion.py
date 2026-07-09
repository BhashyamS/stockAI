from src.committee.schemas import AgentOpinion


class RiskOpinionAgent:
    agent_name = "Risk Agent"
    role = "Evaluates volatility, trend breakdown risk, downside risk, and position safety."

    def run(self, row):
        risk_score = 0
        bullish = []
        bearish = []
        neutral = []
        risks = []

        if row["ATR_Ratio"] > 0.08:
            risk_score += 2
            bearish.append("ATR volatility is high")
            risks.append("High volatility increases downside risk")
        elif row["ATR_Ratio"] > 0.05:
            risk_score += 1
            neutral.append("ATR volatility is moderate")
            risks.append("Moderate volatility requires smaller position sizing")
        else:
            bullish.append("ATR volatility is low")

        if row["Close"] < row["MA_200"]:
            risk_score += 2
            bearish.append("Price is below MA200")
            risks.append("Long-term trend breakdown risk")

        if row["Drop_From_20D_High"] < -0.10:
            risk_score += 1
            bearish.append("Stock is down more than 10% from its 20-day high")
            risks.append("Recent drawdown is significant")

        if row["Momentum_10"] < -0.05:
            risk_score += 1
            bearish.append("10-day momentum is sharply negative")
            risks.append("Short-term downside momentum")

        if risk_score >= 4:
            action = "SELL"
            risk_level = "HIGH"
        elif risk_score >= 2:
            action = "HOLD"
            risk_level = "MEDIUM"
        else:
            action = "BUY"
            risk_level = "LOW"

        confidence = round(min(risk_score / 5, 1), 2)

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
                "risk_score": risk_score,
                "risk_level": risk_level,
                "atr_ratio": row["ATR_Ratio"],
                "price_below_ma200": row["Close"] < row["MA_200"],
                "drop_from_20d_high": row["Drop_From_20D_High"],
                "momentum_10": row["Momentum_10"],
            },
        )