import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TabungEntry(Base):
    __tablename__ = "tabung_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scan_history.id", ondelete="SET NULL")
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_avoided: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    investment_type: Mapped[str | None] = mapped_column(String(50))
    projected_return: Mapped[float | None] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
