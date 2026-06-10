"""
GarageGPT ReAct Agent — Gemini version
Implements a Reason → Act → Observe loop using Gemini's function calling.
"""

import json
import os
import time
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from agent.prompts import SYSTEM_PROMPT, GEMINI_TOOLS
from tools.search_listings import search_listings
from tools.safety_ratings import get_safety_ratings
from tools.fuel_economy import get_fuel_economy
from tools.calculate_tco import calculate_tco

TOOL_REGISTRY = {
    "search_listings":    search_listings,
    "get_safety_ratings": get_safety_ratings,
    "get_fuel_economy":   get_fuel_economy,
    "calculate_tco":      calculate_tco,
}

MAX_ITERATIONS = 10
MAX_RETRIES    = 4
INT_FIELDS     = {"year", "year_min", "max_mileage", "miles_per_year", "years"}
FLOAT_FIELDS   = {"max_price", "price", "mpg"}


def _clean_args(args: dict) -> dict:
    """Drop empty values and coerce numeric types (belt-and-suspenders)."""
    cleaned = {}
    for k, v in args.items():
        if v == "" or v is None:
            continue
        if k in INT_FIELDS:
            cleaned[k] = int(float(v))
        elif k in FLOAT_FIELDS:
            cleaned[k] = float(v)
        else:
            cleaned[k] = v
    return cleaned


class GarageGPTAgent:
    def __init__(self, verbose: bool = True):
        self.client  = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model   = "gemini-2.5-flash"
        self.verbose = verbose
        self.config  = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(function_declarations=GEMINI_TOOLS)],
            temperature=0.2,
        )

    def _log(self, label: str, content: str, color: str = ""):
        if self.verbose:
            print(f"\n{color}[{label}]\033[0m {content}")

    def _call_tool(self, name: str, raw_args: dict) -> dict:
        if name not in TOOL_REGISTRY:
            return {"error": f"unknown tool '{name}'"}
        try:
            args = _clean_args(raw_args)
            self._log("ACTION", f"{name}({args})", "\033[93m")
            return {"result": TOOL_REGISTRY[name](**args)}
        except Exception as e:
            return {"error": f"{name} failed: {str(e)}"}

    def _generate_with_retry(self, contents: list):
        """
        Call Gemini with exponential backoff on transient server errors.
        503 (overloaded), 429 (rate limit), 500 (server) are temporary —
        wait and retry. Other errors (bad key, bad request) raise immediately.
        """
        for attempt in range(MAX_RETRIES):
            try:
                return self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=self.config,
                )
            except genai_errors.ServerError as e:
                # 5xx — Gemini's side. Worth retrying.
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s, 8s
                    self._log("RETRY", f"Gemini busy ({e.code}), waiting {wait}s... ({attempt + 1}/{MAX_RETRIES})", "\033[91m")
                    time.sleep(wait)
                    continue
                raise
            except genai_errors.ClientError as e:
                # 429 rate limit is also worth retrying; other 4xx are not
                if getattr(e, "code", None) == 429 and attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    self._log("RETRY", f"Rate limited, waiting {wait}s... ({attempt + 1}/{MAX_RETRIES})", "\033[91m")
                    time.sleep(wait)
                    continue
                raise
        raise RuntimeError("Gemini unavailable after all retries")

    def run(self, user_query: str) -> str:
        self._log("USER", user_query, "\033[94m")

        # Conversation history as Gemini Content objects
        contents = [types.Content(role="user", parts=[types.Part(text=user_query)])]

        for iteration in range(MAX_ITERATIONS):
            self._log("ITERATION", str(iteration + 1), "\033[90m")

            response = self._generate_with_retry(contents)

            candidate = response.candidates[0]
            parts = candidate.content.parts or []

            # Collect any function calls in this turn
            function_calls = [p.function_call for p in parts if p.function_call]

            if function_calls:
                # Add the model's turn (the function call request) to history
                contents.append(candidate.content)

                # Execute each call and build response parts
                response_parts = []
                for fc in function_calls:
                    raw_args = dict(fc.args)
                    observation = self._call_tool(fc.name, raw_args)
                    obs_str = json.dumps(observation, default=str)
                    self._log("OBSERVATION", obs_str[:400] + ("..." if len(obs_str) > 400 else ""), "\033[92m")

                    response_parts.append(
                        types.Part.from_function_response(
                            name=fc.name,
                            response=observation,
                        )
                    )

                # Add tool results back as a user turn
                contents.append(types.Content(role="user", parts=response_parts))
                continue

            # No function call — this is the final answer
            final = response.text or "No answer generated."
            self._log("FINAL ANSWER", final, "\033[96m")
            return final

        return "Max iterations reached without a final answer."