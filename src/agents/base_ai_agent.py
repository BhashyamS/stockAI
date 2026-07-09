import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Add it to your .env file.")

client = genai.Client(api_key=API_KEY)


class BaseAIAgent:
    def __init__(self, agent_name, role_description):
        self.agent_name = agent_name
        self.role_description = role_description

    def run(self, evidence):
        prompt = f"""
You are {self.agent_name}.

Role:
{self.role_description}

Use ONLY the evidence provided.
Do not invent news, earnings, prices, or external facts.

Return ONLY valid JSON with this exact format:

{{
  "agent_name": "{self.agent_name}",
  "action": "BUY or HOLD or SELL",
  "confidence": 0.0,
  "reasoning": "clear explanation",
  "risks": ["risk 1", "risk 2"],
  "evidence_summary": "short summary"
}}

Evidence:
{json.dumps(evidence, indent=2)}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = response.text.strip()

        # Clean possible markdown formatting
        text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)