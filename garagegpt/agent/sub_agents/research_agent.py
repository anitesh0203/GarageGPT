"""
Research Agent
Owns: search_listings, get_safety_ratings
Job: find matching cars and check their safety scores.
"""

from tools.search_listings import search_listings
from tools.safety_ratings import get_safety_ratings
from agent.sub_agents.base_agent import BaseSubAgent


class ResearchAgent(BaseSubAgent):

    name = "ResearchAgent"

    system_prompt = """You are the Research Agent for GarageGPT.
Your ONLY job is to find matching car listings and check safety ratings.

Rules:
- Always call search_listings first to find real cars
- For the top 2-3 results, call get_safety_ratings for each
- Never calculate costs — that is the Budget Agent's job
- Return a clear summary: car details + safety scores for each candidate
- Be concise — your output feeds into the next agent
"""

    tool_defs = [
        {
            "name": "search_listings",
            "description": "Search for car listings. Only pass parameters the user explicitly mentioned.",
            "parameters": {
                "type": "object",
                "properties": {
                    "make":        {"type": "string",  "description": "Car manufacturer e.g. Honda"},
                    "model":       {"type": "string",  "description": "Car model e.g. CR-V"},
                    "max_price":   {"type": "number",  "description": "Maximum price in USD"},
                    "max_mileage": {"type": "integer", "description": "Maximum mileage"},
                    "year_min":    {"type": "integer", "description": "Minimum model year"},
                },
            },
        },
        {
            "name": "get_safety_ratings",
            "description": "Get NHTSA 5-star safety ratings for a vehicle",
            "parameters": {
                "type": "object",
                "properties": {
                    "make":  {"type": "string",  "description": "Car manufacturer"},
                    "model": {"type": "string",  "description": "Car model"},
                    "year":  {"type": "integer", "description": "Model year"},
                },
                "required": ["make", "model", "year"],
            },
        },
    ]

    tool_registry = {
        "search_listings":    search_listings,
        "get_safety_ratings": get_safety_ratings,
    }
