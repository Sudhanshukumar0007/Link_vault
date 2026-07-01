from datetime import datetime
from uuid import UUID,uuid4
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import func,DateTime

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Provides common metadata configurations and helper methods if needed.
    """
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

