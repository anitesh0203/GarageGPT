"""
Tool: calculate_tco
Estimates the Total Cost of Ownership for a car over N years.
Pure Python — no API, no scraping needed.
"""

def calculate_tco(
    price: float,
    mpg: float,
    years: int = 5,
    miles_per_year: int = 15000,
    gas_price_per_gallon: float = 3.50,
    insurance_per_year: float = 1500.0,
    maintenance_per_year: float = 800.0,
    depreciation_rate: float = 0.15,
) -> dict:
    """
    Estimate total cost of ownership over N years.

    Args:
        price:                  Purchase price in USD
        mpg:                    Miles per gallon (fuel efficiency)
        years:                  How many years the owner plans to keep the car
        miles_per_year:         Average annual mileage
        gas_price_per_gallon:   Current average gas price
        insurance_per_year:     Annual insurance cost estimate
        maintenance_per_year:   Annual maintenance cost estimate
        depreciation_rate:      Annual depreciation as a decimal (e.g. 0.15 = 15%)

    Returns:
        dict with a breakdown of all costs and a total
    """

    # Fuel cost over N years
    total_fuel_cost = (miles_per_year / mpg) * gas_price_per_gallon * years

    # Insurance over N years
    total_insurance = insurance_per_year * years

    # Maintenance over N years
    total_maintenance = maintenance_per_year * years

    # Depreciation: how much value the car loses over N years
    # Uses compound depreciation: value_after = price * (1 - rate)^years
    value_after = price * ((1 - depreciation_rate) ** years)
    total_depreciation = price - value_after

    # Grand total
    total = price + total_fuel_cost + total_insurance + total_maintenance

    return {
        "purchase_price": round(price, 2),
        "years": years,
        "fuel_cost": round(total_fuel_cost, 2),
        "insurance_cost": round(total_insurance, 2),
        "maintenance_cost": round(total_maintenance, 2),
        "depreciation_loss": round(total_depreciation, 2),
        "estimated_resale_value": round(value_after, 2),
        "total_cost_of_ownership": round(total, 2),
        "cost_per_year": round(total / years, 2),
        "cost_per_month": round(total / (years * 12), 2),
    }


if __name__ == "__main__":
    # Quick sanity check
    result = calculate_tco(price=28000, mpg=32, years=5)
    print("TCO breakdown:")
    for key, value in result.items():
        print(f"  {key}: ${value:,.2f}" if isinstance(value, float) else f"  {key}: {value}")