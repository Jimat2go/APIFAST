# Hardcoded for MVP — no DB query needed
# Rates are approximate and for demo purposes

INVESTMENT_OPTIONS = [
    {"name": "ASB",           "rate": 0.055, "is_shariah": False},
    {"name": "Tabung Haji",   "rate": 0.045, "is_shariah": True},
    {"name": "Fixed Deposit", "rate": 0.035, "is_shariah": False},
]


def calculate_projections(principal: float) -> list[dict]:
    """
    Simple annual return projection.
    Formula: projected = principal * (1 + annual_rate)
    """
    results = []
    for option in INVESTMENT_OPTIONS:
        projected = round(principal * (1 + option["rate"]), 2)
        results.append({
            "name": option["name"],
            "rate": option["rate"],
            "projected": projected,
            "gain": round(projected - principal, 2),
            "is_shariah": option["is_shariah"]
        })
    return results
