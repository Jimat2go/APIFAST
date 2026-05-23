from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.scan import ScanHistory
from app.schemas.scan import ScanRequest, ScanResponse
from app.services.gemini_service import analyze_image
from app.services.serp_service import find_alternatives
from app.services.investment_service import calculate_projections
from app.services.scan_service import check_recent_purchase
from datetime import datetime, timezone

router = APIRouter()


@router.post("/analyze", response_model=ScanResponse)
async def analyze(
    body: ScanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Main scan endpoint.
    1. Send image to Gemini → get item + price + impulse check
    2. If impulse → calculate investment projections
    3. If not impulse → call SerpAPI for cheaper alternatives
    4. Save scan to DB
    5. Return full response
    """
    # Step 1 — Gemini analysis
    gemini_result = await analyze_image(body.image_base64)

    # If Gemini says it's not a product, return early
    if not gemini_result.get("is_product", False):
        return ScanResponse(
            is_product=False,
            coach_message=gemini_result.get(
                "coach_message",
                "Hmm, I can't see a product clearly. Try pointing at the item directly.",
            ),
        )

    is_impulse = gemini_result.get("is_impulse", True)
    price = gemini_result.get("price", 0) or 0

    # Step 2/3 — branch on impulse vs necessity
    investment_projections = []
    alternatives = []
    
    is_duplicate = False
    last_bought_days_ago = None
    duplicate_warning = None

    if is_impulse:
        # Calculate what the money could become
        investment_projections = calculate_projections(price)
    else:
        # Check for recent purchases if necessity
        item_name = gemini_result.get("item_name", "")
        if item_name:
            recent_purchase = await check_recent_purchase(db, current_user.id, item_name, days=14)
            if recent_purchase:
                is_duplicate = True
                delta = datetime.now(timezone.utc) - recent_purchase.scanned_at
                last_bought_days_ago = delta.days
                
                duplicate_warning = f"You bought {item_name} {last_bought_days_ago} days ago. Do you really need more? If yes, here's the best price."

        # Find the same item cheaper online
        if item_name and price > 0:
            alternatives = await find_alternatives(item_name, price)

    # Step 4 — persist scan to DB
    scan = ScanHistory(
        user_id=current_user.id,
        item_name=gemini_result.get("item_name"),
        category=gemini_result.get("category"),
        price=price,
        price_source=gemini_result.get("price_source"),
        is_impulse=is_impulse,
        is_duplicate=is_duplicate,
        confidence=gemini_result.get("confidence"),
        coach_message=gemini_result.get("coach_message"),
        gemini_response=gemini_result,
    )
    db.add(scan)
    await db.flush()

    # Step 5 — build response
    return ScanResponse(
        scan_id=scan.id,
        is_product=True,
        item_name=gemini_result.get("item_name"),
        category=gemini_result.get("category"),
        price=price,
        price_source=gemini_result.get("price_source"),
        is_impulse=is_impulse,
        confidence=gemini_result.get("confidence"),
        coach_message=gemini_result.get("coach_message"),
        real_life_equivalents=gemini_result.get("real_life_equivalents", []),
        investment_projections=investment_projections,
        alternatives=alternatives,
        is_duplicate=is_duplicate,
        last_bought_days_ago=last_bought_days_ago,
        duplicate_warning=duplicate_warning,
    )
