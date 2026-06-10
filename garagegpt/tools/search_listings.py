import os
import requests

AUTODEV_URL = "https://api.auto.dev/listings"

DEFAULT_ZIP = "08807"
DEFAULT_DISTANCE = 50

TRACE = True
_GRAY = "\033[90m"
_RESET = "\033[0m"


def _trace(msg: str):
    if TRACE:
        print(f"      {_GRAY}[search_listings] {msg}{_RESET}")


MOCK_LISTINGS = [
    {"make": "Honda",   "model": "CR-V",      "year": 2022, "price": 29500, "mileage": 18000, "location": "Newark, NJ",      "trim": "EX-L",    "color": "Sonic Gray"},
    {"make": "Honda",   "model": "CR-V",      "year": 2021, "price": 27200, "mileage": 31000, "location": "Trenton, NJ",     "trim": "EX",      "color": "Platinum White"},
    {"make": "Toyota",  "model": "RAV4",      "year": 2022, "price": 31000, "mileage": 22000, "location": "Edison, NJ",      "trim": "XLE",     "color": "Magnetic Gray"},
    {"make": "Ford",    "model": "Escape",    "year": 2021, "price": 23800, "mileage": 40000, "location": "Bridgewater, NJ", "trim": "SE",      "color": "Star White"},
    {"make": "Mazda",   "model": "CX-5",      "year": 2021, "price": 27500, "mileage": 33000, "location": "Somerset, NJ",    "trim": "Sport",   "color": "Machine Gray"},
    {"make": "Subaru",  "model": "Forester",  "year": 2022, "price": 28700, "mileage": 21000, "location": "Woodbridge, NJ",  "trim": "Premium", "color": "Crystal Black"},
]


def _search_mock(make, model, max_price, max_mileage, year_min, trim):
    _trace("using MOCK data (no API key or API failed)")
    results = MOCK_LISTINGS.copy()
    if make:
        results = [r for r in results if r["make"].lower() == make.lower()]
    if model:
        results = [r for r in results if model.lower() in r["model"].lower()]
    if trim:
        results = [r for r in results if trim.lower() in r["trim"].lower()]
    if max_price:
        results = [r for r in results if r["price"] <= max_price]
    if max_mileage:
        results = [r for r in results if r["mileage"] <= max_mileage]
    if year_min:
        results = [r for r in results if r["year"] >= year_min]
    results.sort(key=lambda x: x["price"])
    return results


# Reverse geocoding cache — keyed by (lon, lat) -> "City, State"
_geo_cache: dict = {}


def _reverse_geocode(lon: float, lat: float) -> str:
    """Convert [lon, lat] to City, State using OpenStreetMap Nominatim (free, no key)."""
    import time
    key = (round(lon, 4), round(lat, 4))
    if key in _geo_cache:
        return _geo_cache[key]
    try:
        time.sleep(1)
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "GarageGPT/1.0"},
            timeout=5,
        )
        resp.raise_for_status()
        addr = resp.json().get("address", {})
        city  = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("suburb") or ""
        state = addr.get("state", "")
        result = f"{city}, {state}".strip(", ") if (city or state) else f"{lat:.4f}, {lon:.4f}"
    except Exception:
        result = f"{lat:.4f}, {lon:.4f}"
    _geo_cache[key] = result
    _trace(f"geocoded ({lon:.4f}, {lat:.4f}) -> {result}")
    return result


def resolve_location(listing: dict) -> str:
    """
    Geocode a single listing's raw coords to a readable city/state string.
    Call this only on listings you are actually displaying to the user.
    """
    coords = listing.get("_coords")
    if not coords:
        return listing.get("location", "")
    lon, lat = coords
    return _reverse_geocode(lon, lat)


def _parse_listing(item: dict) -> dict:
    v   = item.get("vehicle", {})
    r   = item.get("retailListing", {})
    loc = item.get("location") or []

    # Store raw coords for lazy geocoding — do NOT geocode here
    coords = None
    if isinstance(loc, list) and len(loc) == 2:
        coords = (loc[0], loc[1])

    return {
        "make":     v.get("make", ""),
        "model":    v.get("model", ""),
        "year":     v.get("year", ""),
        "price":    r.get("price", 0),
        "mileage":  v.get("mileage", r.get("miles", 0)),
        "location": "",        # filled lazily via resolve_location()
        "_coords":  coords,    # raw (lon, lat) for geocoding on demand
        "trim":     v.get("trim", ""),
        "vin":      v.get("vin", ""),
        "color":    v.get("color", ""),
    }


def _split_model_and_trim(model: str):
    if not model:
        return None, None
    parts = model.split()
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])


def search_listings(
    make: str = None,
    model: str = None,
    trim: str = None,
    max_price: float = None,
    max_mileage: int = None,
    year_min: int = None,
    zip_code: str = None,
) -> list[dict]:
    # Auto-detect trim if user wrote "X3 M40i"
    if model and not trim:
        model, auto_trim = _split_model_and_trim(model)
        if auto_trim:
            trim = auto_trim

    filters = {k: v for k, v in {
        "make": make, "model": model, "trim": trim,
        "max_price": max_price, "max_mileage": max_mileage, "year_min": year_min
    }.items() if v is not None}
    _trace(f"called with filters: {filters or 'none'}")

    api_key = os.environ.get("AUTODEV_API_KEY")
    if not api_key:
        return _search_mock(make, model, max_price, max_mileage, year_min, trim)

    params = {
        "zip": zip_code or DEFAULT_ZIP,
        "distance": DEFAULT_DISTANCE,
        "sort": "price.asc",
        "limit": 20,
    }
    if make:        params["vehicle.make"]          = make
    if model:       params["vehicle.model"]         = model
    if trim:        params["vehicle.trim"]          = trim
    if year_min:    params["vehicle.year"]          = f"{year_min}-2026"
    if max_price:   params["retailListing.price"]   = f"1-{int(max_price)}"
    if max_mileage: params["vehicle.mileage"]       = f"0-{int(max_mileage)}"

    _trace(f"calling Auto.dev API near {params['zip']}...")

    try:
        resp = requests.get(
            AUTODEV_URL,
            params=params,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict):
            raw_listings = data.get("data", [])
        else:
            raw_listings = data if isinstance(data, list) else []

        results = [_parse_listing(item) for item in raw_listings]
        results = [r for r in results if r["price"]]
        _trace(f"RESULT: {len(results)} real listing(s) from Auto.dev")
        if results:
            c = results[0]
            _trace(f"cheapest: {c['year']} {c['make']} {c['model']} {c.get('trim','')} - ${c['price']:,}")

        # Geocode only the top 5 — the ones agents will actually report
        for listing in results[:5]:
            listing["location"] = resolve_location(listing)

        return results

    except Exception as e:
        _trace(f"API call failed ({e}) — falling back to mock")
        return _search_mock(make, model, max_price, max_mileage, year_min, trim)


if __name__ == "__main__":
    print("\n=== Test: BMW X3 M40i near Bridgewater NJ ===")
    for car in search_listings(make="BMW", model="X3 M40i", year_min=2022):
        print(f"  {car['year']} {car['make']} {car['model']} {car.get('trim','')} — ${car['price']:,} | {car.get('location','')}")