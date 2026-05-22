import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    item_name: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100))
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    price_source: Mapped[str | None] = mapped_column(String(20))
    is_impulse: Mapped[bool | None] = mapped_column(Boolean)
    confidence: Mapped[float | None] = mapped_column(Numeric(3, 2))
    coach_message: Mapped[str | None] = mapped_column(Text)
    action_taken: Mapped[str | None] = mapped_column(String(20))
    gemini_response: Mapped[dict | None] = mapped_column(JSONB)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
