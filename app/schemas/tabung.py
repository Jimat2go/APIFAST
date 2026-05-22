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


class TabungAddResponse(BaseModel):
    entry_id: UUID
    message: str
    tabung_total: float
    projected_return: Optional[float] = None


class TabungSummary(BaseModel):
    total_saved: float
    this_month_saved: float
    items_avoided_count: int
    entries: list[TabungEntryOut]
