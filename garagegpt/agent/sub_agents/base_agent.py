import json, os, time
from groq import Groq, BadRequestError

MAX_ITERATIONS = 8
MAX_RETRIES    = 4
INT_FIELDS     = {"year", "year_min", "max_mileage", "miles_per_year", "years"}
FLOAT_FIELDS   = {"max_price", "price", "mpg"}

def _clean_args(args: dict) -> dict:
    if not args:
        return {}
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

class BaseSubAgent:
    name: str = "BaseAgent"
    tool_defs: list = []
    tool_registry: dict = {}
    system_prompt: str = ""

    def __init__(self, verbose: bool = True):
        self.client  = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model   = "llama-3.1-8b-instant"
        self.verbose = verbose

    def _log(self, label, content, color=""):
        if self.verbose:
            print(f"\n  {color}[{self.name} → {label}]\033[0m {content}")

    def _call_tool(self, name, raw_args):
        if name not in self.tool_registry:
            return {"error": f"unknown tool '{name}'"}
        try:
            args = _clean_args(raw_args)
            self._log("ACTION", f"{name}({args})", "\033[93m")
            return {"result": self.tool_registry[name](**args)}
        except Exception as e:
            return {"error": f"{name} failed: {str(e)}"}

    def _llm_call(self, messages):
        for attempt in range(MAX_RETRIES):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=[{"type": "function", "function": t} for t in self.tool_defs] if self.tool_defs else None,
                    tool_choice="auto" if self.tool_defs else None,
                    temperature=0.2,
                )
            except BadRequestError as e:
                if "tool_use_failed" in str(e) and attempt < MAX_RETRIES - 1:
                    self._log("RETRY", f"Bad tool call, retrying ({attempt+1}/{MAX_RETRIES})...", "\033[91m")
                    time.sleep(1)
                    continue
                raise
        raise RuntimeError("All retries exhausted")

    def run(self, user_query: str, context: str = "") -> str:
        full_input = user_query
        if context:
            full_input = f"{user_query}\n\nContext from previous analysis:\n{context}"

        self._log("START", f'"{user_query[:60]}"', "\033[94m")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user",   "content": full_input},
        ]

        for iteration in range(MAX_ITERATIONS):
            self._log("ITERATION", str(iteration + 1), "\033[90m")
            response = self._llm_call(messages)
            message  = response.choices[0].message

            if message.tool_calls:
                # Clean args before storing in history
                clean_calls = []
                for tc in message.tool_calls:
                    raw  = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    clean_calls.append({
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.function.name, "arguments": json.dumps(_clean_args(raw))},
                    })

                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": clean_calls,
                })

                for tc, cc in zip(message.tool_calls, clean_calls):
                    observation = self._call_tool(tc.function.name, json.loads(tc.function.arguments) if tc.function.arguments else {})
                    obs_str = json.dumps(observation, default=str)
                    self._log("OBSERVATION", obs_str[:300] + ("..." if len(obs_str) > 300 else ""), "\033[92m")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": obs_str,
                    })
                continue

            result = message.content or "No result."
            self._log("DONE", result[:200] + ("..." if len(result) > 200 else ""), "\033[96m")
            return result

        return "Max iterations reached."