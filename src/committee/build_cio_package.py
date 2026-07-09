import json
from pathlib import Path

INPUT_JSON = Path("data/processed/structured_committee_results.json")
OUTPUT_JSON = Path("data/processed/cio_prompt_packages.json")


def build_package(result):
    opinions = result["vote_summary"]["opinions"]

    return {
        "ticker": result["ticker"],
        "committee_decision": result["weighted_vote"]["final_action"],
        "committee_score": result["weighted_vote"]["committee_score"],
        "vote_details": result["weighted_vote"]["vote_details"],
        "debate": result["debate"],
        "agent_reports": [
            {
                "agent": opinion["agent_name"],
                "role": opinion["role"],
                "action": opinion["action"],
                "confidence": opinion["confidence"],
                "bullish_evidence": opinion["bullish_evidence"],
                "bearish_evidence": opinion["bearish_evidence"],
                "neutral_evidence": opinion["neutral_evidence"],
                "risks": opinion["risks"],
                "evidence": opinion["evidence"],
            }
            for opinion in opinions
        ],
    }


def main():
    with open(INPUT_JSON, "r") as f:
        results = json.load(f)

    packages = [build_package(result) for result in results]

    with open(OUTPUT_JSON, "w") as f:
        json.dump(packages, f, indent=2)

    print(f"Saved CIO prompt packages to {OUTPUT_JSON}")
    print(json.dumps(packages[0], indent=2)[:1500])


if __name__ == "__main__":
    main()