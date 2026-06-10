import json, os, time
from groq import Groq

from agent.sub_agents.research_agent    import ResearchAgent
from agent.sub_agents.budget_agent      import BudgetAgent
from agent.sub_agents.negotiation_agent import NegotiationAgent

MAX_RETRIES = 4

MERGER_PROMPT = """You are GarageGPT, an expert AI car buying advisor.
Merge the specialist agent findings into one clear final answer.
Lead with the top recommendation, include key numbers (price, safety, MPG, 5yr cost),
and end with negotiation advice if provided. Be direct and specific."""


class Orchestrator:
    def __init__(self, verbose: bool = True):
        self.client  = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model   = "llama-3.1-8b-instant"
        self.verbose = verbose
        self. research    = ResearchAgent(verbose=verbose)
        self.budget      = BudgetAgent(verbose=verbose)
        self.negotiation = NegotiationAgent(verbose=verbose)
        # Persists across queries — each turn stored as {query, answer}
        self.conversation_history: list[dict] = []

    def clear_history(self):
        """Reset conversation — useful for starting a new topic."""
        self.conversation_history = []
        self._log("MEMORY", "Conversation history cleared", "\033[90m")

    def _log(self, label, content, color=""):
        if self.verbose:
            print(f"\n\033[1m{color}[ORCHESTRATOR → {label}]\033[0m {content}")

    def _groq_call(self, user_msg: str, system: str) -> str:
        for attempt in range(MAX_RETRIES):
            try:
                r = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user_msg},
                    ],
                    temperature=0.1,
                )
                return r.choices[0].message.content or ""
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise

    def _plan(self, user_query: str) -> list:
        q = user_query.lower()
        budget_words      = ["cost", "price", "tco", "afford", "expensive", "cheap",
                             "budget", "mpg", "fuel", "monthly", "own", "spend"]
        negotiation_words = ["negotiate", "deal", "offer", "discount", "worth",
                             "should i buy", "good deal", "fair price", "haggle"]
        agents = ["research"]
        if any(w in q for w in budget_words):
            agents.append("budget")
        if any(w in q for w in negotiation_words):
            agents.append("negotiation")
        if len(agents) == 1:
            agents.append("budget")
        self._log("PLAN", f"agents={agents} (keyword routing)", "\033[95m")
        return agents

    def _merge(self, user_query: str, results: dict) -> str:
        self._log("MERGING", "Combining all agent results...", "\033[95m")
        combined = f"User question: {user_query}\n\n"
        for name, result in results.items():
            combined += f"=== {name.upper()} AGENT ===\n{result}\n\n"
        return self._groq_call(combined, MERGER_PROMPT)

    def _build_context_from_history(self) -> str:
        """Build a context string from past conversation turns."""
        if not self.conversation_history:
            return ""
        ctx = "=== CONVERSATION HISTORY ===\n"
        for turn in self.conversation_history[-3:]:   # last 3 turns only (token efficiency)
            ctx += f"User: {turn['query']}\nGarageGPT: {turn['answer']}\n\n"
        return ctx

    def run(self, user_query: str) -> str:
        print(f"\n{'='*60}")
        self._log("USER QUERY", user_query, "\033[94m")
        if self.conversation_history:
            self._log("MEMORY", f"{len(self.conversation_history)} previous turn(s) in context", "\033[90m")
        print(f"{'='*60}")

        agents_to_run = self._plan(user_query)
        results  = {}

        # Seed context with conversation history so agents know what was discussed
        context = self._build_context_from_history()

        if "research" in agents_to_run:
            self._log("CALLING", "Research Agent", "\033[95m")
            r = self.research.run(user_query, context)
            results["research"] = r
            context += f"RESEARCH FINDINGS:\n{r}\n\n"

            if self._research_found_nothing(r):
                self._log("STOP", "Research found no cars — skipping downstream agents", "\033[91m")
                final = (
                    "I couldn't find any listings matching your criteria. "
                    "Try widening your search — different make/model, higher price ceiling, or older year."
                )
                print(f"\n{'='*60}")
                print(f"\033[1m\033[96m[FINAL ANSWER]\033[0m\n{final}")
                print(f"{'='*60}\n")
                # Still save to history so next query can reference "couldn't find X"
                self.conversation_history.append({"query": user_query, "answer": final})
                return final

        if "budget" in agents_to_run:
            self._log("CALLING", "Budget Agent", "\033[95m")
            r = self.budget.run(user_query, context)
            results["budget"] = r
            context += f"BUDGET ANALYSIS:\n{r}\n\n"

        if "negotiation" in agents_to_run:
            self._log("CALLING", "Negotiation Agent", "\033[95m")
            r = self.negotiation.run(user_query, context)
            results["negotiation"] = r

        final = list(results.values())[0] if len(results) == 1 else self._merge(user_query, results)

        # Save this turn to history
        self.conversation_history.append({"query": user_query, "answer": final})

        print(f"\n{'='*60}")
        print(f"\033[1m\033[96m[FINAL ANSWER]\033[0m\n{final}")
        print(f"{'='*60}\n")
        return final

    def _research_found_nothing(self, research_result: str) -> bool:
        text = research_result.lower()
        signals = ["couldn't find", "could not find", "no listings", "no cars",
                   "no results", "no matching", "unable to find", "didn't find"]
        return any(s in text for s in signals)