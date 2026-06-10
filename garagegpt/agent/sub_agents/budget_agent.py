"""
Budget Agent
Owns: get_fuel_economy, calculate_tco
Job: calculate the real cost of owning each car the Research Agent found.
"""

from tools.fuel_economy import get_fuel_economy
from tools.calculate_tco import calculate_tco
from agent.sub_agents.base_agent import BaseSubAgent


class BudgetAgent(BaseSubAgent):

    name = "BudgetAgent"

    system_prompt = """You are the Budget Agent for GarageGPT.
Your ONLY job is to calculate the true cost of owning each car.

You will receive a list of cars from the Research Agent.
For each car:
1. Call get_fuel_economy to get the MPG
2. Call calculate_tco using the car's price and that MPG

CRITICAL: If the research context contains NO actual cars (empty results, or a
message saying nothing was found), do NOT invent any cars, prices, or numbers.
Simply respond: "No cars available to analyze." Never make up data.

Rules:
- Cover every car mentioned in the research context
- Always use the combined_mpg from get_fuel_economy as the mpg for calculate_tco
- Return a clear cost breakdown per car: purchase price, fuel, 5-year total, per month
- Never research new cars — only analyze what Research Agent found
"""

    tool_defs = [
        {
            "name": "get_fuel_economy",
            "description": "Get EPA fuel economy (MPG) data for a vehicle",
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
        {
            "name": "calculate_tco",
            "description": "Calculate total cost of ownership over N years",
            "parameters": {
                "type": "object",
                "properties": {
                    "price":          {"type": "number",  "description": "Purchase price in USD"},
                    "mpg":            {"type": "number",  "description": "Combined MPG"},
                    "years":          {"type": "integer", "description": "Years to own (default 5)"},
                    "miles_per_year": {"type": "integer", "description": "Annual mileage (default 15000)"},
                },
                "required": ["price", "mpg"],
            },
        },
    ]

    tool_registry = {
        "get_fuel_economy": get_fuel_economy,
        "calculate_tco":    calculate_tco,
    }