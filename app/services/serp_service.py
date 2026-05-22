from serpapi import GoogleSearch
from app.core.config import settings


async def find_alternatives(item_name: str, current_price: float) -> list[dict]:
    """
    Search for item on Malaysian e-commerce. Return up to 3 cheaper options.
    Returns [] silently if SerpAPI fails — never break the main flow.
    """
    try:
        params = {
            "engine": "google_shopping",
            "q": f"{item_name} Malaysia",
            "location": "Malaysia",
            "hl": "en",
            "gl": "my",
            "api_key": settings.SERPAPI_API_KEY,
            "num": 20
        }

        results = GoogleSearch(params).get_dict()
        shopping = results.get("shopping_results", [])

        alternatives = []
        seen_platforms = set()

        for item in shopping:
            price_str = item.get("price", "")
            link = item.get("link", "") or item.get("product_link", "")
            source = (item.get("source", "") + " " + link).lower()

            # Parse price
            try:
                price_val = float(
                    price_str.replace("RM", "").replace(",", "").strip()
                )
            except (ValueError, AttributeError):
                continue

            # Only cheaper
            if price_val >= current_price:
                continue

            # Detect platform
            platform = None
            if "shopee" in source:   platform = "Shopee"
            elif "lazada" in source: platform = "Lazada"
            elif "tiktok" in source: platform = "TikTok Shop"

            if not platform or platform in seen_platforms:
                continue

            seen_platforms.add(platform)
            alternatives.append({
                "platform": platform,
                "title": item.get("title", "")[:80],
                "price": round(price_val, 2),
                "url": link,
                "savings": round(current_price - price_val, 2)
            })

            if len(alternatives) >= 3:
                break

        return sorted(alternatives, key=lambda x: x["price"])

    except Exception:
        return []   # fail silently — never crash the scan endpoint
