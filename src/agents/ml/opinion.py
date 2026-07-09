from src.committee.schemas import AgentOpinion


class MLOpinionAgent:
    agent_name = "ML Agent"
    role = "Evaluates machine learning probability, model confidence, and statistical edge."

    def run(self, row):
        prob = row["ML_Prob_5D_Up"]

        bullish = []
        bearish = []
        neutral = []
        risks = []

        if prob >= 0.60:
            action = "BUY"
            bullish.append("ML model predicts elevated probability of 5-day upside")
        elif prob <= 0.45:
            action = "SELL"
            bearish.append("ML model predicts weak probability of 5-day upside")
        else:
            action = "HOLD"
            neutral.append("ML model does not show a strong statistical edge")

        confidence = round(abs(prob - 0.50) * 2, 2)

        if confidence < 0.20:
            risks.append("Model confidence is weak")

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
                "ml_probability_5d_up": prob,
                "ml_signal": row.get("ML_Signal", action),
                "model_confidence": confidence,
            },
        )