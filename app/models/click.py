from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    link_id: Mapped[UUID] = mapped_column(ForeignKey("links.id"), nullable=False, index=True)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=True)
    device_type: Mapped[str] = mapped_column(String(20), nullable=True)
    browser: Mapped[str] = mapped_column(String(50), nullable=True)
    referrer: Mapped[str] = mapped_column(String(500), nullable=True)