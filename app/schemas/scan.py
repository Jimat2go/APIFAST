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
    is_duplicate: Optional[bool] = False
    last_bought_days_ago: Optional[int] = None
    duplicate_warning: Optional[str] = None
