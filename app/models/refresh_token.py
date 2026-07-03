from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from datetime import datetime
from sqlalchemy import String,Boolean,ForeignKey,DateTime
from app.db.base import Base,TimestampMixin

class RefreshToken(Base,TimestampMixin):
    __tablename__ = "refresh_tokens"
    id : Mapped[UUID] = mapped_column(
        primary_key = True,
        default = uuid4,
        index = True
    )

    token_hash : Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False
    )

    user_id:Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable = False
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default = False,
        nullable = False
    )
