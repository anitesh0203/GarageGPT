"""
Prompts and tool schema definitions for GarageGPT agent (Gemini version).
"""

SYSTEM_PROMPT = """You are GarageGPT, an expert AI car buying advisor for the US market.
You help people find the right used or new car based on their needs and budget.

You have access to tools to search listings, get safety ratings, get fuel economy data, and calculate total cost of ownership.

Rules:
- Always call search_listings first to find actual cars before analyzing them
- For each shortlisted car, fetch safety ratings and fuel economy
- Always calculate TCO for final recommendations using the combined_mpg from get_fuel_economy
- Never make up data — only use what tools return
- Be specific and concrete — include price, safety stars, MPG, and 5-year cost in your final answer
- If comparing multiple cars, rank them clearly
- Only pass parameters the user actually mentioned; omit the rest
"""

# Gemini function declarations — note: type names are UPPERCASE per Gemini's schema
GEMINI_TOOLS = [
    {
        "name": "search_listings",
        "description": "Search for car listings. Only pass parameters the user explicitly mentioned.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "make":        {"type": "STRING",  "description": "Car manufacturer e.g. Honda, Toyota"},
                "model":       {"type": "STRING",  "description": "Car model e.g. CR-V, RAV4"},
                "max_price":   {"type": "NUMBER",  "description": "Maximum price in USD e.g. 30000"},
                "max_mileage": {"type": "INTEGER", "description": "Maximum mileage e.g. 50000"},
                "year_min":    {"type": "INTEGER", "description": "Minimum model year e.g. 2020"},
            },
        },
    },
    {
        "name": "get_safety_ratings",
        "description": "Fetch NHTSA 5-star safety ratings for a vehicle",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "make":  {"type": "STRING",  "description": "Car manufacturer"},
                "model": {"type": "STRING",  "description": "Car model"},
                "year":  {"type": "INTEGER", "description": "Model year e.g. 2022"},
            },
            "required": ["make", "model", "year"],
        },
    },
    {
        "name": "get_fuel_economy",
        "description": "Fetch EPA fuel economy (MPG) data for a vehicle",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "make":  {"type": "STRING",  "description": "Car manufacturer"},
                "model": {"type": "STRING",  "description": "Car model"},
                "year":  {"type": "INTEGER", "description": "Model year e.g. 2022"},
            },
            "required": ["make", "model", "year"],
        },
    },
    {
        "name": "calculate_tco",
        "description": "Calculate Total Cost of Ownership over N years",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "price":          {"type": "NUMBER",  "description": "Purchase price in USD"},
                "mpg":            {"type": "NUMBER",  "description": "Combined MPG"},
                "years":          {"type": "INTEGER", "description": "Number of years to own the car"},
                "miles_per_year": {"type": "INTEGER", "description": "Annual mileage estimate"},
            },
            "required": ["price", "mpg"],
        },
    },
]