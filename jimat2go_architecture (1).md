# Jimat2go — MVP Architecture & Project Documentation

> **Project:** Jimat2go  
> **Hackathon:** BeU by Bank Islam × UMPSA × Fintech Forward 2026  
> **Theme:** Future of Money — Reimagine Finance with AI  
> **Stack:** Flutter · FastAPI (Python) · Google Gemini 1.5 Flash · SerpAPI · PostgreSQL  
> **Mode:** MVP — fast, working, impressive. Not production-hardened.

---

## Table of Contents

1. [What This App Does (Plain English)](#1-what-this-app-does-plain-english)
2. [The Big Change — No OCR, Gemini Sees Everything](#2-the-big-change--no-ocr-gemini-sees-everything)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Full App Flow Step by Step](#4-full-app-flow-step-by-step)
5. [Database Schema](#5-database-schema)
6. [FastAPI Backend Structure](#6-fastapi-backend-structure)
7. [API Endpoints](#7-api-endpoints)
8. [Gemini Service — The Brain](#8-gemini-service--the-brain)
9. [SerpAPI Service](#9-serpapi-service)
10. [Investment Calculator](#10-investment-calculator)
11. [Flutter Structure](#11-flutter-structure)
12. [Pydantic Schemas](#12-pydantic-schemas)
13. [Environment Variables](#13-environment-variables)
14. [Folder Structure + requirements.txt](#14-folder-structure--requirementstxt)
15. [MVP Scope — What to Skip](#15-mvp-scope--what-to-skip)

---

## 1. What This App Does (Plain English)

Jimat2go is an AI financial coach that lives in your camera.

You're standing in a mall holding an air fryer. You open the app, point the camera at it, tap once. Gemini looks at the image and tells you:

- What the item is
- How much it costs (reads the price tag if visible, otherwise estimates from market knowledge)
- Whether it's an impulse buy or a genuine need
- If impulse → what that money could become instead (ASB returns, real-life equivalents)
- If not impulse → find the same thing cheaper on Shopee or Lazada

The user taps "Save It" and the money they didn't spend goes into their virtual Tabung — a running total of avoided spending.

---

## 2. The Big Change — No OCR, Gemini Sees Everything

### Old Idea (scrapped)
```
Camera → ML Kit OCR reads price tag → send price + image to backend
```
Problem: OCR is fragile. Messy tags, angles, lighting — it breaks easily. Also adds a Flutter dependency just for one task.

### New MVP Approach
```
Camera → capture image → send ONLY the image to Gemini → Gemini does everything
```

Gemini 1.5 Flash is multimodal. It can look at a photo and:

| Scenario | What Gemini Does |
|---|---|
| Clear price tag visible | Reads the price directly from the tag |
| No price tag, recognizable product | Identifies the product, estimates Malaysian market price |
| Ambiguous item | Makes best guess, flags low confidence |
| Not a product (e.g. food stall, person) | Returns `is_product: false` |

This is simpler code, more impressive demo, and works in more real-world situations. One API call does it all.

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│               FLUTTER MOBILE APP                    │
│                                                     │
│  Camera Screen                                      │
│    → User taps "Scan"                               │
│    → Capture JPEG frame                             │
│    → Convert to base64                              │
│    → POST to /scan/analyze                          │
│                                                     │
│  Result Screen                                      │
│    → Show item name + estimated price               │
│    → Coach message / alternatives                   │
│    → Save It / Invest It buttons                    │
│                                                     │
│  Tabung Screen                                      │
│    → Running total of avoided spending              │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS REST (JSON)
                   ▼
┌─────────────────────────────────────────────────────┐
│             FASTAPI BACKEND (Python)                │
│                                                     │
│  POST /scan/analyze                                 │
│    1. Decode base64 image                           │
│    2. Send image to Gemini → get item + price       │
│    3. IF impulse → calculate investment returns     │
│    4. IF not impulse → call SerpAPI for alternatives│
│    5. Save scan to DB                               │
│    6. Return full response                          │
│                                                     │
│  POST /tabung/add                                   │
│  GET  /tabung/summary                               │
│  POST /auth/register + /auth/login                  │
└──────┬────────────────┬────────────────┬────────────┘
       │                │                │
       ▼                ▼                ▼
┌────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Gemini     │  │  SerpAPI     │  │   PostgreSQL     │
│ 1.5 Flash  │  │  (Shopping)  │  │   Database       │
│            │  │              │  │                  │
│ - See item │  │ - Shopee     │  │ - users          │
│ - Read tag │  │ - Lazada     │  │ - scan_history   │
│ - Estimate │  │ - TikTok     │  │ - tabung_entries │
│   price    │  │   Shop       │  │ - invest_options │
└────────────┘  └──────────────┘  └──────────────────┘
```

---

## 4. Full App Flow Step by Step

### Step 1 — Auth (one time)
```
User opens app
→ Register: POST /auth/register { name, email, password }
← { access_token, user_id }

Token stored in flutter_secure_storage
All requests carry: Authorization: Bearer <token>
```

---

### Step 2 — Camera Screen
```
Flutter shows live camera preview
User points at any product — phone, air fryer, sneakers, whatever
User taps the big scan button

Flutter does:
  1. cameraController.takePicture()         → XFile
  2. File(image.path).readAsBytes()         → Uint8List
  3. base64Encode(bytes)                    → String
  4. POST /scan/analyze { image_base64 }
```

No OCR. No price detection on device. Just capture and send. That's it.

---

### Step 3 — Gemini Analyzes the Image

Backend receives the image and sends it to Gemini with a detailed prompt.

Gemini looks at the image and figures out:
- What is this product
- Is there a visible price tag? If yes, read it. If no, estimate market price in RM.
- Is this an impulse purchase or a necessity
- What coaching message to show
- What real-life equivalents apply at this price

**Gemini returns structured JSON. See Section 8 for the full prompt.**

Example Gemini output for an air fryer photo:
```json
{
  "is_product": true,
  "item_name": "Philips Air Fryer HD9200",
  "category": "Kitchen Appliance",
  "price_source": "estimated",
  "price": 299.00,
  "currency": "MYR",
  "is_impulse": true,
  "confidence": 0.88,
  "coach_message": "Third kitchen gadget this month? The old one is still in the box. RM 299 can fly you somewhere instead.",
  "real_life_equivalents": [
    { "icon": "✈️", "label": "Return flight to Penang" },
    { "icon": "🛒", "label": "2 months of groceries" },
    { "icon": "📱", "label": "6 months of Spotify" }
  ]
}
```

Example for a phone with visible price tag:
```json
{
  "is_product": true,
  "item_name": "Samsung Galaxy A55",
  "category": "Smartphone",
  "price_source": "tag",
  "price": 1599.00,
  "currency": "MYR",
  "is_impulse": true,
  "confidence": 0.95,
  "coach_message": "Your current phone still works fine. RM 1,599 invested in ASB for 5 years becomes RM 2,078.",
  "real_life_equivalents": [
    { "icon": "✈️", "label": "Return flight to Tokyo" },
    { "icon": "🎓", "label": "One semester of college fees" },
    { "icon": "💰", "label": "5 months emergency fund" }
  ]
}
```

`price_source` tells Flutter whether to show "Price from tag: RM X" or "Estimated price: ~RM X"

---

### Step 4a — If is_impulse = true

Backend calculates investment projections using the price from Gemini:
```
ASB          → price × 1.055  (5.5% annual)
Tabung Haji  → price × 1.045  (4.5% annual)
Fixed Deposit → price × 1.035 (3.5% annual)
```

SerpAPI is NOT called. No need to find alternatives for impulse items.

Backend response includes coach message + equivalents + investment projections.

---

### Step 4b — If is_impulse = false

Backend calls SerpAPI to find the same item cheaper online.

Query: `"{item_name}" buy Malaysia`  
Filter: only Shopee, Lazada, TikTok Shop results cheaper than Gemini's price.  
Return: top 3 sorted by lowest price.

Backend response includes alternatives list. No investment projections shown.

---

### Step 5 — Flutter Shows Result Screen

**Impulse Flow:**
```
┌──────────────────────────────────────┐
│  Air Fryer                           │
│  Estimated price: ~RM 299            │
│                                      │
│  "Third kitchen gadget this month?   │
│   RM 299 can fly you somewhere."     │
│                                      │
│  ✈️  Return flight to Penang        │
│  🛒  2 months groceries              │
│  📱  6 months Spotify                │
│                                      │
│  If you invest RM 299 instead:       │
│  ASB         → RM 315  (+RM 16)      │
│  Tabung Haji → RM 312  (+RM 13)      │
│  Fixed Dep.  → RM 309  (+RM 10)      │
│                                      │
│  [💰 Save It]    [📈 Invest It]      │
└──────────────────────────────────────┘
```

**Not Impulse Flow:**
```
┌──────────────────────────────────────┐
│  Rice Cooker                         │
│  Price from tag: RM 299              │
│                                      │
│  Looks like you need this.           │
│  But here's where to buy it cheaper: │
│                                      │
│  Shopee      RM 239   [Open]         │
│  Lazada      RM 259   [Open]         │
│  TikTok Shop RM 229   [Open]         │
│                                      │
│  [💰 Save RM 70 difference]          │
└──────────────────────────────────────┘
```

---

### Step 6 — User Saves to Tabung
```
POST /tabung/add
{
  "scan_id": "uuid",
  "item_name": "Air Fryer",
  "price_avoided": 299.00,
  "action": "invest",          // or "save"
  "investment_type": "ASB"     // or null if action=save
}

← {
  "message": "RM 299 added to your Tabung!",
  "tabung_total": 1240.00
}
```

---

### Step 7 — My Tabung Dashboard
```
GET /tabung/summary

← {
  "total_saved": 1240.00,
  "this_month_saved": 488.00,
  "items_avoided_count": 4,
  "entries": [ ... ]
}
```

---

## 5. Database Schema

```sql
-- Users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Every scan the user does
CREATE TABLE scan_history (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_name        VARCHAR(255),
    category         VARCHAR(100),
    price            DECIMAL(10,2),
    price_source     VARCHAR(20),      -- 'tag' or 'estimated'
    is_impulse       BOOLEAN,
    confidence       DECIMAL(3,2),
    coach_message    TEXT,
    action_taken     VARCHAR(20),      -- 'save', 'invest', 'ignored'
    gemini_response  JSONB,            -- store full Gemini JSON for debugging
    scanned_at       TIMESTAMP DEFAULT NOW()
);

-- Every time user saves/invests to Tabung
CREATE TABLE tabung_entries (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scan_id          UUID REFERENCES scan_history(id) ON DELETE SET NULL,
    item_name        VARCHAR(255) NOT NULL,
    amount_avoided   DECIMAL(10,2) NOT NULL,
    action           VARCHAR(20) NOT NULL,      -- 'save' or 'invest'
    investment_type  VARCHAR(50),               -- 'ASB', 'tabung_haji', 'fixed_deposit'
    projected_return DECIMAL(10,2),
    created_at       TIMESTAMP DEFAULT NOW()
);

-- Investment options (seeded, not user-editable)
CREATE TABLE investment_options (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    annual_rate  DECIMAL(5,4) NOT NULL,
    is_shariah   BOOLEAN DEFAULT false,
    is_active    BOOLEAN DEFAULT true
);

INSERT INTO investment_options (name, annual_rate, is_shariah) VALUES
  ('ASB',           0.0550, false),
  ('Tabung Haji',   0.0450, true),
  ('Fixed Deposit', 0.0350, false);
```

---

## 6. FastAPI Backend Structure

```
jimat2go-backend/
├── main.py
├── requirements.txt
├── .env
│
└── app/
    ├── core/
    │   ├── config.py          # Settings (reads .env)
    │   ├── database.py        # SQLAlchemy async engine + get_db()
    │   ├── security.py        # JWT sign/verify, bcrypt hash/verify
    │   └── dependencies.py    # get_current_user() FastAPI dependency
    │
    ├── models/                # SQLAlchemy ORM table definitions
    │   ├── user.py
    │   ├── scan.py
    │   ├── tabung.py
    │   └── investment.py
    │
    ├── schemas/               # Pydantic request/response models
    │   ├── auth.py
    │   ├── scan.py
    │   └── tabung.py
    │
    ├── routers/               # FastAPI route handlers
    │   ├── auth.py            # /auth/*
    │   ├── scan.py            # /scan/*
    │   └── tabung.py          # /tabung/*
    │
    └── services/              # Business logic (no DB calls here)
        ├── gemini_service.py  # Image → Gemini → structured result
        ├── serp_service.py    # Item name → SerpAPI → alternatives
        └── investment_service.py  # Price → projected returns
```

---

## 7. API Endpoints

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get token |
| GET | `/auth/me` | Get current user |

**POST /auth/register**
```json
// Request
{ "name": "Amirah", "email": "amirah@mail.com", "password": "pass123" }

// Response 201
{ "access_token": "eyJ...", "token_type": "bearer" }
```

**POST /auth/login**
```json
// Request
{ "email": "amirah@mail.com", "password": "pass123" }

// Response 200
{ "access_token": "eyJ...", "token_type": "bearer" }
```

---

### Scan

| Method | Path | Description |
|---|---|---|
| POST | `/scan/analyze` | Main endpoint — image in, full result out |

**POST /scan/analyze**
```json
// Request
{
  "image_base64": "<base64 jpeg string>"
}

// Response 200 — impulse item
{
  "scan_id": "uuid",
  "is_product": true,
  "item_name": "Philips Air Fryer",
  "category": "Kitchen Appliance",
  "price": 299.00,
  "price_source": "estimated",       // or "tag" if price tag was visible
  "is_impulse": true,
  "confidence": 0.88,
  "coach_message": "Third kitchen gadget this month?",
  "real_life_equivalents": [
    { "icon": "✈️", "label": "Return flight to Penang" },
    { "icon": "🛒", "label": "2 months groceries" },
    { "icon": "📱", "label": "6 months Spotify" }
  ],
  "investment_projections": [
    { "name": "ASB",           "rate": 0.055, "projected": 315.45, "gain": 16.45 },
    { "name": "Tabung Haji",   "rate": 0.045, "projected": 312.46, "gain": 13.46 },
    { "name": "Fixed Deposit", "rate": 0.035, "projected": 309.47, "gain": 10.47 }
  ],
  "alternatives": []
}

// Response 200 — necessity item
{
  "scan_id": "uuid",
  "is_product": true,
  "item_name": "Rice Cooker Panasonic",
  "category": "Kitchen Appliance",
  "price": 299.00,
  "price_source": "tag",
  "is_impulse": false,
  "confidence": 0.85,
  "coach_message": null,
  "real_life_equivalents": [],
  "investment_projections": [],
  "alternatives": [
    { "platform": "Shopee",    "title": "Panasonic SR-W18", "price": 239.00, "url": "...", "savings": 60.00 },
    { "platform": "Lazada",    "title": "Panasonic Rice Cooker 1.8L", "price": 259.00, "url": "...", "savings": 40.00 },
    { "platform": "TikTok Shop","title": "Panasonic SR W18 Original", "price": 229.00, "url": "...", "savings": 70.00 }
  ]
}

// Response 200 — not a product
{
  "scan_id": null,
  "is_product": false,
  "item_name": null,
  "coach_message": "Hmm, I can't see a product clearly. Try pointing at the item directly."
}
```

---

### Tabung

| Method | Path | Description |
|---|---|---|
| POST | `/tabung/add` | Save an avoided purchase |
| GET | `/tabung/summary` | Get total + entry list |
| DELETE | `/tabung/entry/{id}` | Remove an entry |

**POST /tabung/add**
```json
// Request
{
  "scan_id": "uuid",
  "item_name": "Air Fryer",
  "price_avoided": 299.00,
  "action": "invest",
  "investment_type": "ASB"
}

// Response 201
{
  "entry_id": "uuid",
  "message": "RM 299.00 saved! Tabung is now RM 1,240.00",
  "tabung_total": 1240.00,
  "projected_return": 315.45
}
```

**GET /tabung/summary**
```json
// Response 200
{
  "total_saved": 1240.00,
  "this_month_saved": 488.00,
  "items_avoided_count": 4,
  "entries": [
    {
      "id": "uuid",
      "item_name": "Air Fryer",
      "amount_avoided": 299.00,
      "action": "invest",
      "investment_type": "ASB",
      "projected_return": 315.45,
      "created_at": "2026-05-20T14:32:00Z"
    }
  ]
}
```

---

## 8. Gemini Service — The Brain

### File: `app/services/gemini_service.py`

```python
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
```

---

## 9. SerpAPI Service

### File: `app/services/serp_service.py`

```python
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
```

---

## 10. Investment Calculator

### File: `app/services/investment_service.py`

```python
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
```

No database call. No async. Just math. Perfect for MVP.

---

## 11. Flutter Structure

```
lib/
├── main.dart
│
├── core/
│   ├── api_client.dart        # Dio instance, base URL, auth interceptor
│   ├── auth_storage.dart      # flutter_secure_storage wrapper
│   └── constants.dart
│
├── models/
│   ├── scan_result.dart       # Maps the /scan/analyze response
│   └── tabung_entry.dart
│
├── providers/                 # Riverpod state
│   ├── auth_provider.dart
│   ├── scan_provider.dart
│   └── tabung_provider.dart
│
└── screens/
    ├── auth/
    │   ├── login_screen.dart
    │   └── register_screen.dart
    ├── camera_screen.dart     # Live preview + tap to scan
    ├── result_screen.dart     # Show AI result + CTA
    ├── invest_sheet.dart      # Bottom sheet: pick ASB / TH / FD
    └── tabung_screen.dart     # My Tabung dashboard
```

### Camera Screen — Core Logic (Simplified)

```dart
// Tap to scan — just capture the frame and send it
Future<void> onScanTapped() async {
  final XFile image = await cameraController.takePicture();
  final bytes = await File(image.path).readAsBytes();
  final base64Image = base64Encode(bytes);

  // Send to backend — Gemini handles everything else
  await ref.read(scanProvider.notifier).analyze(base64Image);
  Navigator.pushNamed(context, '/result');
}
```

No ML Kit. No regex. No OCR logic. Just capture, encode, send. Clean.

### Flutter Packages Needed (pubspec.yaml)
```yaml
dependencies:
  camera: ^0.10.5
  dio: ^5.4.0
  flutter_riverpod: ^2.5.1
  flutter_secure_storage: ^9.0.0
  fl_chart: ^0.67.0
```

---

## 12. Pydantic Schemas

### `app/schemas/scan.py`
```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class ScanRequest(BaseModel):
    image_base64: str


class RealLifeEquivalent(BaseModel):
    icon: str
    label: str


class InvestmentProjection(BaseModel):
    name: str
    rate: float
    projected: float
    gain: float


class Alternative(BaseModel):
    platform: str
    title: str
    price: float
    url: str
    savings: float


class ScanResponse(BaseModel):
    scan_id: Optional[UUID] = None
    is_product: bool
    item_name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    price_source: Optional[str] = None     # "tag" or "estimated"
    is_impulse: Optional[bool] = None
    confidence: Optional[float] = None
    coach_message: Optional[str] = None
    real_life_equivalents: list[RealLifeEquivalent] = []
    investment_projections: list[InvestmentProjection] = []
    alternatives: list[Alternative] = []
```

### `app/schemas/tabung.py`
```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class TabungAddRequest(BaseModel):
    scan_id: Optional[UUID] = None
    item_name: str
    price_avoided: float
    action: str                            # 'save' or 'invest'
    investment_type: Optional[str] = None  # 'ASB', 'tabung_haji', 'fixed_deposit'


class TabungEntryOut(BaseModel):
    id: UUID
    item_name: str
    amount_avoided: float
    action: str
    investment_type: Optional[str]
    projected_return: Optional[float]
    created_at: datetime


class TabungSummary(BaseModel):
    total_saved: float
    this_month_saved: float
    items_avoided_count: int
    entries: list[TabungEntryOut]
```

---

## 13. Environment Variables

```env
# .env

# JWT
SECRET_KEY=some_long_random_string_at_least_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database (use Supabase free tier or Railway Postgres for hackathon)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/jimat2go

# Gemini
GEMINI_API_KEY=AIzaSy...

# SerpAPI
SERPAPI_API_KEY=abc123...
```

### `app/core/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    DATABASE_URL: str
    GEMINI_API_KEY: str
    SERPAPI_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 14. Folder Structure + requirements.txt

```
jimat2go-backend/
├── main.py
├── requirements.txt
├── .env
│
└── app/
    ├── core/
    │   ├── config.py
    │   ├── database.py
    │   ├── security.py
    │   └── dependencies.py
    ├── models/
    │   ├── user.py
    │   ├── scan.py
    │   ├── tabung.py
    │   └── investment.py
    ├── schemas/
    │   ├── auth.py
    │   ├── scan.py
    │   └── tabung.py
    ├── routers/
    │   ├── auth.py
    │   ├── scan.py
    │   └── tabung.py
    └── services/
        ├── gemini_service.py
        ├── serp_service.py
        └── investment_service.py
```

### `requirements.txt`
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.7.1
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
pillow==10.3.0
google-generativeai==0.5.4
google-search-results==2.4.2
```

### `main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, scan, tabung

app = FastAPI(title="Jimat2go API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,   prefix="/auth",   tags=["Auth"])
app.include_router(scan.router,   prefix="/scan",   tags=["Scan"])
app.include_router(tabung.router, prefix="/tabung", tags=["Tabung"])

@app.get("/health")
def health():
    return {"status": "ok", "app": "Jimat2go"}
```

---

## 15. MVP Scope — What to Skip

This is a hackathon. Build what matters. Skip everything else.

### Build These
- [x] Auth (register + login, JWT)
- [x] Camera screen (capture + send)
- [x] Gemini scan endpoint (identify item + price + impulse check)
- [x] Investment projection cards
- [x] SerpAPI alternatives (nice to have, skip if tight on time)
- [x] Tabung add + summary screen
- [x] Basic UI with working flow end-to-end

### Skip These for Now
- [ ] Email verification
- [ ] Forgot password flow
- [ ] Image storage (don't store images in DB or cloud — waste of time)
- [ ] Pagination on history
- [ ] Push notifications
- [ ] Social sharing
- [ ] Advanced charts / analytics
- [ ] Caching layer (Redis etc)
- [ ] Rate limiting
- [ ] Unit tests

### Hackathon Database Tip
Use **Supabase** free tier. You get a hosted PostgreSQL database in 2 minutes, no setup, accessible via `DATABASE_URL`. No need to run Postgres locally or configure anything.

### Hackathon Hosting Tip
Deploy FastAPI to **Railway** or **Render** free tier. Push to GitHub, connect repo, set env vars, done. Your Flutter app just needs the deployed URL.

---

*Jimat2go — BeU by Bank Islam × UMPSA × Fintech Forward 2026*  
*Flutter · FastAPI · Gemini 1.5 Flash · SerpAPI · PostgreSQL*
