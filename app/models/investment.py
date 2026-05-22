from sqlalchemy import String, Numeric, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class InvestmentOption(Base):
    __tablename__ = "investment_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    annual_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    is_shariah: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
