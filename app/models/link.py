from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin
from sqlalchemy import DateTime

class Link(Base, TimestampMixin):
    __tablename__ = "links"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True
    )

    slug: Mapped[str] = mapped_column(
        String(12),
        unique=True,
        index=True
    )

    original_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    expires_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=True
    )

    click_count: Mapped[int] = mapped_column(
        default=0
    )