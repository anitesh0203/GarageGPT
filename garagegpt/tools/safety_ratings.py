"""
Tool: get_safety_ratings
Fetches NHTSA crash test safety ratings (free, official US government API).
Docs: https://api.nhtsa.gov/SafetyRatings
"""

import requests

BASE_URL = "https://api.nhtsa.gov/SafetyRatings"

# ── Mock data fallback ────────────────────────────────────────────────────────
MOCK_SAFETY_DATA = {
    ("honda",   "cr-v",     2022): {"overall": 5, "frontal": 5, "side": 5, "rollover": 4, "rollover_risk": "10.5%"},
    ("toyota",  "rav4",     2022): {"overall": 5, "frontal": 5, "side": 5, "rollover": 4, "rollover_risk": "11.2%"},
    ("ford",    "escape",   2022): {"overall": 4, "frontal": 4, "side": 5, "rollover": 4, "rollover_risk": "12.1%"},
    ("mazda",   "cx-5",     2022): {"overall": 5, "frontal": 5, "side": 5, "rollover": 5, "rollover_risk": "9.8%"},
    ("subaru",  "forester", 2022): {"overall": 5, "frontal": 5, "side": 5, "rollover": 4, "rollover_risk": "10.9%"},
    ("hyundai", "tucson",   2022): {"overall": 4, "frontal": 4, "side": 5, "rollover": 4, "rollover_risk": "11.8%"},
}


def get_safety_ratings(make: str, model: str, year: int) -> dict:
    """
    Fetch NHTSA 5-star safety ratings for a vehicle.
    Tries live API first, falls back to mock data.

    Args:
        make:   e.g. 'Honda'
        model:  e.g. 'CR-V'
        year:   e.g. 2022

    Returns:
        dict with overall, frontal, side, rollover ratings (out of 5 stars)
    """
    # Try live API
    try:
        url = f"{BASE_URL}/modelyear/{year}/make/{make}/model/{model}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("Results", [])
        if results:
            r = results[0]
            return {
                "make": make, "model": model, "year": year,
                "overall": r.get("OverallRating"),
                "frontal": r.get("OverallFrontCrashRating"),
                "side": r.get("OverallSideCrashRating"),
                "rollover": r.get("RolloverRating"),
                "rollover_risk": r.get("RolloverPossibility"),
                "source": "NHTSA API (live)",
            }
    except Exception:
        pass  # Fall through to mock

    # Mock fallback
    key = (make.lower(), model.lower(), year)
    if key in MOCK_SAFETY_DATA:
        mock = MOCK_SAFETY_DATA[key]
        return {"make": make, "model": model, "year": year, **mock, "source": "mock data"}

    return {"error": f"No safety data found for {year} {make} {model}"}


if __name__ == "__main__":
    print("Testing safety ratings: 2022 Mazda CX-5")
    result = get_safety_ratings("Mazda", "CX-5", 2022)
    for k, v in result.items():
        print(f"  {k}: {v}")