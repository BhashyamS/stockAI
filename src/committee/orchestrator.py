from src.committee.voting_engine import VotingEngine
from src.committee.debate_engine import DebateEngine
from src.committee.committee_memory import CommitteeMemory


class InvestmentCommitteeOrchestrator:
    def __init__(self, agents):
        self.agents = agents
        self.voting_engine = VotingEngine()
        self.debate_engine = DebateEngine()
        self.memory = CommitteeMemory()

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

    def run_committee(self, ticker_data):
        opinions = self.collect_opinions(ticker_data)

        vote_summary = self.summarize_votes(opinions)
        weighted_vote = self.voting_engine.score_opinions(opinions)
        debate = self.debate_engine.build_debate_points(opinions)

        result = {
            "ticker": ticker_data["Ticker"],
            "vote_summary": vote_summary,
            "weighted_vote": weighted_vote,
            "debate": debate,
        }

        self.memory.save_record(ticker_data["Ticker"], result)

        return result