ACTION_SCORE = {
    "BUY": 1,
    "HOLD": 0,
    "SELL": -1,
}

AGENT_WEIGHTS = {
    "Technical Agent": 0.35,
    "ML Agent": 0.30,
    "Risk Agent": 0.35,
}


class VotingEngine:
    def __init__(self, weights=None):
        self.weights = weights or AGENT_WEIGHTS

    def score_opinions(self, opinions):
        weighted_score = 0
        total_weight = 0

        vote_details = []

        for opinion in opinions:
            weight = self.weights.get(opinion.agent_name, 0.25)
            action_score = ACTION_SCORE.get(opinion.action, 0)

            contribution = action_score * opinion.confidence * weight

            weighted_score += contribution
            total_weight += weight

            vote_details.append({
                "agent": opinion.agent_name,
                "action": opinion.action,
                "confidence": opinion.confidence,
                "weight": weight,
                "contribution": contribution,
            })

        normalized_score = weighted_score / total_weight if total_weight else 0

        if normalized_score >= 0.25:
            final_action = "BUY"
        elif normalized_score <= -0.25:
            final_action = "SELL"
        else:
            final_action = "HOLD"

        return {
            "final_action": final_action,
            "committee_score": round(normalized_score, 3),
            "vote_details": vote_details,
        }