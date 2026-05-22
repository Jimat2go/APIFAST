import google.generativeai as genai
import base64
import json
from PIL import Image
import io
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


GEMINI_PROMPT = """
You are the AI brain inside Jimat2go, a Malaysian personal finance app that helps
young people avoid impulse spending.

A user just pointed their phone camera at something. Analyze the image and return
a JSON object. Nothing else. No explanation, no markdown, no backticks.

YOUR JOB:
1. Figure out what product is in the image (if any)
2. Find the price — read the price tag if one is visible, otherwise estimate
   the current Malaysian market price in Ringgit (RM)
3. Decide if this is an impulse purchase or a genuine necessity
4. Generate a coaching response

PRICE DETECTION RULES:
- If you can see a clear price tag in the image → use that price, set price_source = "tag"
- If no price tag visible but you recognize the product → estimate Malaysian retail
  price, set price_source = "estimated"
- If you cannot identify the product → set is_product = false

IMPULSE vs NECESSITY:
- IMPULSE: wants, not needs — gadgets, fashion, extra appliances, decorations,
  collectibles, accessories, luxury items, duplicate items user likely already owns
- NECESSITY: food, medicine, basic household items, school/work supplies,
  first-time essential appliances

COACH MESSAGE RULES:
- Only write if is_impulse = true
- Friendly, slightly cheeky, Malaysian style English
- Max 2 sentences
- Never shame — just reframe
- Reference the amount and what it could do instead

REAL LIFE EQUIVALENTS RULES:
- Only if is_impulse = true
- Generate exactly 3, based on the price
- Use Malaysian context: Grab rides, teh tarik, nasi lemak, Astro bill,
  flight to Langkawi/Penang/Sabah, monthly TNB bill, PTPTN installment, etc
- RM 0-50:   small daily equivalents (meals, rides, subscriptions)
- RM 50-200: weekly/monthly bills or short trips
- RM 200-500: domestic flights, months of bills
- RM 500+:   international travel, semester fees, emergency fund months

RESPOND ONLY WITH THIS JSON:
{
  "is_product": true or false,
  "item_name": "string or null",
  "category": "string or null",
  "price": number or null,
  "price_source": "tag" or "estimated" or null,
  "is_impulse": true or false or null,
  "confidence": float 0.0-1.0,
  "coach_message": "string or null",
  "real_life_equivalents": [
    { "icon": "emoji", "label": "string" }
  ]
}
"""


FALLBACK_RESPONSE = {
    "is_product": True,
    "item_name": "Unknown Item",
    "category": "General",
    "price": 100.00,
    "price_source": "estimated",
    "is_impulse": True,
    "confidence": 0.5,
    "coach_message": "Take a breath before buying. Your future self will thank you.",
    "real_life_equivalents": [
        {"icon": "🍱", "label": "5 days of lunch"},
        {"icon": "📱", "label": "2 months Spotify"},
        {"icon": "🚗", "label": "10 Grab rides"}
    ]
}


async def analyze_image(image_base64: str) -> dict:
    """
    Send image to Gemini. Returns structured dict.
    Falls back gracefully if Gemini fails or returns bad JSON.
    """
    try:
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))

        response = model.generate_content([GEMINI_PROMPT, image])

        raw = response.text.strip()

        # Strip markdown code fences if Gemini wraps in ```json ... ```
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        result = json.loads(raw)
        return result

    except json.JSONDecodeError:
        return FALLBACK_RESPONSE
    except Exception:
        return FALLBACK_RESPONSE
