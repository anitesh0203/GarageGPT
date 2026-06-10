"""
run_single_agent.py — Trigger ONE agent directly, bypassing the orchestrator.
Useful for testing/debugging a single agent in isolation.

Usage:
    python run_single_agent.py research "safe SUV under 28000"
    python run_single_agent.py budget   "Honda CR-V 2022 at 29500"
    python run_single_agent.py negotiate "Mazda CX-5 at 27500, 5/5 safety, 30 mpg"
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

from agent.sub_agents.research_agent    import ResearchAgent
from agent.sub_agents.budget_agent      import BudgetAgent
from agent.sub_agents.negotiation_agent import NegotiationAgent


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_single_agent.py <research|budget|negotiate> \"your query\"")
        sys.exit(1)

    which = sys.argv[1].lower()
    query = sys.argv[2]

    # For budget/negotiate, you can pass context as a 3rd arg
    context = sys.argv[3] if len(sys.argv) > 3 else ""

    if which == "research":
        agent = ResearchAgent(verbose=True)
        result = agent.run(query)
    elif which == "budget":
        agent = BudgetAgent(verbose=True)
        # If no context given, treat the query itself as the car description
        result = agent.run(query, context or query)
    elif which in ("negotiate", "negotiation"):
        agent = NegotiationAgent(verbose=True)
        result = agent.run(query, context or query)
    else:
        print(f"Unknown agent: {which}. Use research, budget, or negotiate.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"RESULT FROM {which.upper()} AGENT:")
    print(f"{'='*60}")
    print(result)


if __name__ == "__main__":
    main()