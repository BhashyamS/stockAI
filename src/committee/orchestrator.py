class InvestmentCommitteeOrchestrator:
    def __init__(self, agents):
        self.agents = agents

    def collect_opinions(self, ticker_data):
        opinions = []

        for agent in self.agents:
            opinion = agent.run(ticker_data)
            opinions.append(opinion)

        return opinions

    def summarize_votes(self, opinions):
        return {
            "opinions": [opinion.to_dict() for opinion in opinions],
            "buy_votes": sum(1 for o in opinions if o.action == "BUY"),
            "hold_votes": sum(1 for o in opinions if o.action == "HOLD"),
            "sell_votes": sum(1 for o in opinions if o.action == "SELL"),
            "avg_confidence": sum(o.confidence for o in opinions) / len(opinions),
        }