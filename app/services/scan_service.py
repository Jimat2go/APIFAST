import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.scan import ScanHistory

async def check_recent_purchase(
    db: AsyncSession,
    user_id: uuid.UUID, 
    item_name: str, 
    days: int = 14
) -> ScanHistory | None:
    """
    Queries scan_history for the same item_name within X days for the user.
    Returns the most recent scan record if found, else None.
    """
    if not item_name:
        return None

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    stmt = (
        select(ScanHistory)
        .where(
            ScanHistory.user_id == user_id,
            ScanHistory.scanned_at >= cutoff_date
        )
        .order_by(ScanHistory.scanned_at.desc())
    )
    
    result = await db.execute(stmt)
    recent_scans = result.scalars().all()
    
    item_name_lower = item_name.lower()
    for scan in recent_scans:
        db_item_name = (scan.item_name or "").lower()
        if db_item_name and (db_item_name in item_name_lower or item_name_lower in db_item_name):
            return scan
            
    return None
