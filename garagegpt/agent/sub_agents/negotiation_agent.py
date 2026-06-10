import os, time
from groq import Groq

MAX_RETRIES = 4

SYSTEM_PROMPT = """You are the Negotiation Agent for GarageGPT — an expert car buying negotiator.

You will receive research and budget analysis for one or more cars.

Your job:
1. Pick the best overall value car based on safety + cost
2. Assess whether the listed price is fair, high, or a bargain
3. Give 3 specific actionable negotiation tips for that car
4. Give a recommended offer price (typically 5-8% below asking)

Be direct, specific, and use the actual numbers from the context."""

class NegotiationAgent:
    name = "NegotiationAgent"

    def __init__(self, verbose: bool = True):
        self.client  = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model   = "llama-3.1-8b-instant"
        self.verbose = verbose

    def _log(self, label, content, color=""):
        if self.verbose:
            print(f"\n  {color}[{self.name} → {label}]\033[0m {content}")

    def run(self, user_query: str, context: str = "") -> str:
        self._log("START", "Analyzing deal and preparing negotiation advice...", "\033[94m")
        full_input = (
            f"User's question: {user_query}\n\n"
            f"Research and budget analysis:\n{context}\n\n"
            f"Give your negotiation assessment and recommendation."
        )
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": full_input},
                    ],
                    temperature=0.3,
                )
                result = response.choices[0].message.content or "No advice generated."
                self._log("DONE", result[:200] + "...", "\033[96m")
                return result
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError("Negotiation agent unavailable.")