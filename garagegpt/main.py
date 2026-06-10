"""
GarageGPT — main entry point (Phase 3: Multi-Agent)
"""

import os
from dotenv import load_dotenv
from agent.orchestrator import Orchestrator

load_dotenv()

def main():
    print("\n🚗  GarageGPT — AI Car Buying Advisor (Multi-Agent Mode)")
    print("    Commands: 'quit' to exit, 'clear' to reset conversation\n")

    agent = Orchestrator(verbose=True)

    while True:
        try:
            query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if query.lower() == "clear":
            agent.clear_history()
            print("Conversation cleared. Starting fresh.")
            continue

        agent.run(query)


if __name__ == "__main__":
    main()