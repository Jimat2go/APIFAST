from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.tabung import TabungEntry
from app.schemas.tabung import (
    TabungAddRequest,
    TabungAddResponse,
    TabungSummary,
    TabungEntryOut,
)
from app.services.investment_service import calculate_projections

router = APIRouter()


@router.post("/add", response_model=TabungAddResponse, status_code=status.HTTP_201_CREATED)
async def add_entry(
    body: TabungAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save an avoided purchase to the user's Tabung."""
    # Calculate projected return if investing
    projected_return = None
    if body.action == "invest" and body.investment_type:
        projections = calculate_projections(body.price_avoided)
        for p in projections:
            if p["name"].lower().replace(" ", "_") == body.investment_type.lower().replace(" ", "_"):
                projected_return = p["projected"]
                break
        # Fallback: if investment_type name doesn't match exactly, use first
        if projected_return is None and projections:
            projected_return = projections[0]["projected"]

    entry = TabungEntry(
        user_id=current_user.id,
        scan_id=body.scan_id,
        item_name=body.item_name,
        amount_avoided=body.price_avoided,
        action=body.action,
        investment_type=body.investment_type,
        projected_return=projected_return,
    )
    db.add(entry)
    await db.flush()

    # Calculate running total
    total_result = await db.execute(
        select(func.coalesce(func.sum(TabungEntry.amount_avoided), 0))
        .where(TabungEntry.user_id == current_user.id)
    )
    tabung_total = float(total_result.scalar())

    return TabungAddResponse(
        entry_id=entry.id,
        message=f"RM {body.price_avoided:.2f} saved! Tabung is now RM {tabung_total:,.2f}",
        tabung_total=tabung_total,
        projected_return=projected_return,
    )


@router.get("/summary", response_model=TabungSummary)
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's Tabung summary — totals + entry list."""
    now = datetime.now(timezone.utc)

    # All entries for this user
    result = await db.execute(
        select(TabungEntry)
        .where(TabungEntry.user_id == current_user.id)
        .order_by(TabungEntry.created_at.desc())
    )
    entries = result.scalars().all()

    total_saved = sum(float(e.amount_avoided) for e in entries)
    this_month = sum(
        float(e.amount_avoided) for e in entries
        if e.created_at.month == now.month and e.created_at.year == now.year
    )

    return TabungSummary(
        total_saved=total_saved,
        this_month_saved=this_month,
        items_avoided_count=len(entries),
        entries=[
            TabungEntryOut(
                id=e.id,
                item_name=e.item_name,
                amount_avoided=float(e.amount_avoided),
                action=e.action,
                investment_type=e.investment_type,
                projected_return=float(e.projected_return) if e.projected_return else None,
                created_at=e.created_at,
            )
            for e in entries
        ],
    )


@router.delete("/entry/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a Tabung entry."""
    result = await db.execute(
        select(TabungEntry).where(
            TabungEntry.id == entry_id,
            TabungEntry.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

    await db.delete(entry)
