from uuid import UUID, uuid4
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base,TimestampMixin

class User(Base,TimestampMixin):
    __tablename__ = "users"

    id:Mapped[UUID] = mapped_column(
        primary_key = True,
        default = uuid4,
        index = True
    )
    name: Mapped[str] = mapped_column(
    String(100),
    nullable=False
    )
    email : Mapped[str] = mapped_column(
        String(265),
        unique = True,
        index = True,
        nullable = False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(265),
        nullable = False
    )

    is_active : Mapped[bool] = mapped_column(
        Boolean,
        default = True,
        nullable = False
    )

    plan:Mapped[str] = mapped_column(
        String(50),
        default = 'free',
        nullable = False
    )