class DebateEngine:
    def detect_disagreement(self, opinions):
        actions = set(opinion.action for opinion in opinions)
        return len(actions) > 1

    def build_debate_points(self, opinions):
        debate = []

        for opinion in opinions:
            debate.append({
                "agent": opinion.agent_name,
                "position": opinion.action,
                "confidence": opinion.confidence,
                "bullish_case": opinion.bullish_evidence,
                "bearish_case": opinion.bearish_evidence,
                "risks": opinion.risks,
            })

        disagreement = self.detect_disagreement(opinions)

        return {
            "has_disagreement": disagreement,
            "debate_points": debate,
            "summary": (
                "Agents disagree, so the CIO should weigh conflicting evidence."
                if disagreement
                else "Agents broadly agree."
            ),
        }