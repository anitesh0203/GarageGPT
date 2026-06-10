"""
GarageGPT MCP Server (Phase 2)
================================
Exposes the SAME four tools from Phase 1 over the Model Context Protocol,
so Claude Desktop (or any MCP client) can call them directly.

Note: there is NO Gemini and NO ReAct loop here. Claude Desktop is the brain.
This file only exposes the tools. That's the whole point of MCP.

Run locally to test:   python server.py
Or with the inspector:  mcp dev server.py
"""

import json
from mcp.server.fastmcp import FastMCP

# Import the EXACT same tool functions from Phase 1 — unchanged.
from tools.search_listings import search_listings as _search_listings
from tools.safety_ratings import get_safety_ratings as _get_safety_ratings
from tools.fuel_economy import get_fuel_economy as _get_fuel_economy
from tools.calculate_tco import calculate_tco as _calculate_tco

# Create the MCP server. The name shows up in Claude Desktop.
mcp = FastMCP("garagegpt")


# ──────────────────────────────────────────────────────────────────────────────
# Each @mcp.tool() wraps one Phase-1 tool.
# The docstring + type hints ARE the schema — Claude reads them to know how to
# call the tool. This replaces the GEMINI_TOOLS schema we wrote by hand before.
# We return formatted STRINGS (not raw dicts) — Claude Desktop can truncate dicts.
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_listings(
    make: str = "",
    model: str = "",
    max_price: float = 0,
    max_mileage: int = 0,
    year_min: int = 0,
) -> str:
    """Search for used car listings matching the given criteria.

    Args:
        make: Car manufacturer e.g. Honda, Toyota. Leave empty for any.
        model: Car model e.g. CR-V, RAV4. Leave empty for any.
        max_price: Maximum price in USD. Use 0 for no limit.
        max_mileage: Maximum mileage. Use 0 for no limit.
        year_min: Minimum model year. Use 0 for no limit.
    """
    # Convert the "empty" sentinels into None/omitted for the real function
    kwargs = {}
    if make:        kwargs["make"] = make
    if model:       kwargs["model"] = model
    if max_price:   kwargs["max_price"] = max_price
    if max_mileage: kwargs["max_mileage"] = max_mileage
    if year_min:    kwargs["year_min"] = year_min

    results = _search_listings(**kwargs)
    if not results:
        return "No listings found matching those criteria."

    lines = [f"Found {len(results)} listings:\n"]
    for c in results:
        lines.append(
            f"- {c['year']} {c['make']} {c['model']} {c['trim']} — "
            f"${c['price']:,} | {c['mileage']:,} mi | {c['location']}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_safety_ratings(make: str, model: str, year: int) -> str:
    """Get NHTSA 5-star crash safety ratings for a specific vehicle.

    Args:
        make: Car manufacturer e.g. Honda.
        model: Car model e.g. CR-V.
        year: Model year e.g. 2022.
    """
    r = _get_safety_ratings(make, model, year)
    if "error" in r:
        return r["error"]
    return (
        f"Safety ratings for {r['year']} {r['make']} {r['model']}:\n"
        f"- Overall: {r['overall']}/5 stars\n"
        f"- Frontal crash: {r['frontal']}/5\n"
        f"- Side crash: {r['side']}/5\n"
        f"- Rollover: {r['rollover']}/5 (risk: {r.get('rollover_risk', 'n/a')})"
    )


@mcp.tool()
def get_fuel_economy(make: str, model: str, year: int) -> str:
    """Get EPA fuel economy (MPG) data for a specific vehicle.

    Args:
        make: Car manufacturer e.g. Toyota.
        model: Car model e.g. RAV4.
        year: Model year e.g. 2022.
    """
    r = _get_fuel_economy(make, model, year)
    if "error" in r:
        return r["error"]
    return (
        f"Fuel economy for {r['year']} {r['make']} {r['model']}:\n"
        f"- City: {r.get('city_mpg')} MPG\n"
        f"- Highway: {r.get('highway_mpg')} MPG\n"
        f"- Combined: {r.get('combined_mpg')} MPG\n"
        f"- Estimated annual fuel cost: ${r.get('annual_fuel_cost', 'n/a')}"
    )


@mcp.tool()
def calculate_tco(price: float, mpg: float, years: int = 5, miles_per_year: int = 15000) -> str:
    """Calculate the total cost of ownership for a car over N years.

    Args:
        price: Purchase price in USD.
        mpg: Combined miles per gallon.
        years: Number of years to own the car (default 5).
        miles_per_year: Average annual mileage (default 15000).
    """
    r = _calculate_tco(price=price, mpg=mpg, years=years, miles_per_year=miles_per_year)
    return (
        f"Total cost of ownership over {r['years']} years:\n"
        f"- Purchase price: ${r['purchase_price']:,.0f}\n"
        f"- Fuel: ${r['fuel_cost']:,.0f}\n"
        f"- Insurance: ${r['insurance_cost']:,.0f}\n"
        f"- Maintenance: ${r['maintenance_cost']:,.0f}\n"
        f"- Total: ${r['total_cost_of_ownership']:,.0f}\n"
        f"- Per month: ${r['cost_per_month']:,.0f}\n"
        f"- Estimated resale value: ${r['estimated_resale_value']:,.0f}"
    )


if __name__ == "__main__":
    # stdio transport — Claude Desktop launches this as a subprocess
    mcp.run()