from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class AgentOpinion:
    agent_name: str
    role: str
    ticker: str
    action: str
    confidence: float
    bullish_evidence: List[str]
    bearish_evidence: List[str]
    neutral_evidence: List[str]
    risks: List[str]
    evidence: Dict[str, Any]

    def to_dict(self):
        return asdict(self)