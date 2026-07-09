import json
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path("data/committee_memory.json")
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)


class CommitteeMemory:
    def load_memory(self):
        if not MEMORY_FILE.exists():
            return []

        with open(MEMORY_FILE, "r") as f:
            return json.load(f)

    def save_record(self, ticker, committee_result):
        memory = self.load_memory()

        memory.append({
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "committee_result": committee_result,
        })

        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)

    def get_ticker_history(self, ticker, limit=5):
        memory = self.load_memory()

        records = [
            item for item in memory
            if item["ticker"] == ticker
        ]

        return records[-limit:]