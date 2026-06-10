"""
Tool: get_fuel_economy
Fetches official EPA fuel economy data from FuelEconomy.gov (free, no API key needed).
Docs: https://www.fueleconomy.gov/feg/ws/index.shtml
"""

import requests


BASE_URL = "https://www.fueleconomy.gov/ws/rest"


def _get_makes(year: int) -> list[str]:
    """Return all available makes for a given year."""
    url = f"{BASE_URL}/vehicle/menu/make?year={year}"
    resp = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("menuItem", [])
    if isinstance(items, dict):
        items = [items]
    return [item["value"] for item in items]


def _get_models(year: int, make: str) -> list[str]:
    """Return all available models for a given year and make."""
    url = f"{BASE_URL}/vehicle/menu/model?year={year}&make={make}"
    resp = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("menuItem", [])
    if isinstance(items, dict):
        items = [items]
    return [item["value"] for item in items]


def _get_vehicle_ids(year: int, make: str, model: str) -> list[int]:
    """Return vehicle IDs matching year/make/model."""
    url = f"{BASE_URL}/vehicle/menu/options?year={year}&make={make}&model={model}"
    resp = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("menuItem", [])
    if isinstance(items, dict):
        items = [items]
    return [int(item["value"]) for item in items]


def _get_vehicle_data(vehicle_id: int) -> dict:
    """Fetch full vehicle data for a given ID."""
    url = f"{BASE_URL}/vehicle/{vehicle_id}"
    resp = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_fuel_economy(make: str, model: str, year: int) -> dict:
    """
    Fetch EPA fuel economy data for a specific vehicle.

    Args:
        make:   Car manufacturer e.g. 'Honda', 'Toyota'
        model:  Car model e.g. 'CR-V', 'RAV4'
        year:   Model year e.g. 2022

    Returns:
        dict with city/highway/combined MPG and other fuel data,
        or an error message if not found.
    """
    try:
        vehicle_ids = _get_vehicle_ids(year, make, model)
    except Exception as e:
        return {"error": f"Could not find vehicle {year} {make} {model}: {str(e)}"}

    if not vehicle_ids:
        return {"error": f"No data found for {year} {make} {model}"}

    # Take the first matching variant (e.g. base trim)
    vehicle_id = vehicle_ids[0]

    try:
        data = _get_vehicle_data(vehicle_id)
    except Exception as e:
        return {"error": f"Could not fetch vehicle data: {str(e)}"}

    return {
        "make": data.get("make"),
        "model": data.get("model"),
        "year": data.get("year"),
        "city_mpg": data.get("city08"),
        "highway_mpg": data.get("highway08"),
        "combined_mpg": data.get("comb08"),
        "fuel_type": data.get("fuelType"),
        "engine": data.get("displ"),
        "cylinders": data.get("cylinders"),
        "transmission": data.get("trany"),
        "co2_per_mile": data.get("co2"),
        "annual_fuel_cost": data.get("fuelCost08"),
        "vehicle_class": data.get("VClass"),
    }



# ── Mock data (used when API is unreachable, e.g. sandbox environments) ──────
MOCK_FUEL_DATA = {
    ("honda",   "cr-v",   2022): {"city_mpg": 28, "highway_mpg": 34, "combined_mpg": 30, "fuel_type": "Regular", "annual_fuel_cost": 2050},
    ("toyota",  "rav4",   2022): {"city_mpg": 27, "highway_mpg": 35, "combined_mpg": 30, "fuel_type": "Regular", "annual_fuel_cost": 2100},
    ("ford",    "escape", 2022): {"city_mpg": 27, "highway_mpg": 33, "combined_mpg": 30, "fuel_type": "Regular", "annual_fuel_cost": 2050},
    ("mazda",   "cx-5",   2022): {"city_mpg": 25, "highway_mpg": 31, "combined_mpg": 28, "fuel_type": "Regular", "annual_fuel_cost": 2200},
    ("subaru",  "forester", 2022): {"city_mpg": 26, "highway_mpg": 33, "combined_mpg": 29, "fuel_type": "Regular", "annual_fuel_cost": 2150},
    ("hyundai", "tucson", 2022): {"city_mpg": 26, "highway_mpg": 33, "combined_mpg": 29, "fuel_type": "Regular", "annual_fuel_cost": 2150},
}

def get_fuel_economy(make: str, model: str, year: int) -> dict:
    """
    Fetch EPA fuel economy data. Tries live API first, falls back to mock data.
    """
    # Try live API first
    try:
        vehicle_ids = _get_vehicle_ids(year, make, model)
        if vehicle_ids:
            data = _get_vehicle_data(vehicle_ids[0])
            return {
                "make": data.get("make"), "model": data.get("model"), "year": data.get("year"),
                "city_mpg": data.get("city08"), "highway_mpg": data.get("highway08"),
                "combined_mpg": data.get("comb08"), "fuel_type": data.get("fuelType"),
                "annual_fuel_cost": data.get("fuelCost08"), "vehicle_class": data.get("VClass"),
                "source": "fueleconomy.gov (live)",
            }
    except Exception:
        pass  # Fall through to mock

    # Mock fallback
    key = (make.lower(), model.lower(), year)
    if key in MOCK_FUEL_DATA:
        mock = MOCK_FUEL_DATA[key]
        return {"make": make, "model": model, "year": year, **mock, "source": "mock data"}

    return {"error": f"No fuel economy data found for {year} {make} {model}"}


if __name__ == "__main__":
    print("Testing fuel economy lookup: 2022 Honda CR-V")
    result = get_fuel_economy("Honda", "CR-V", 2022)
    for k, v in result.items():
        print(f"  {k}: {v}")