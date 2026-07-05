from uuid import UUID,uuid4
from sqlalchemy import String,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base,TimestampMixin

class Workspace(Base,TimestampMixin):
    __tablename__ = "workspaces"

    id:Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True
    )
    
    name:Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    owner_id:Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    plan: Mapped[str] = mapped_column(
        String(50),
        default="free",
        nullable = False
    )

class WorkspaceMember(Base,TimestampMixin):
    __tablename__ = "workspace_members"

    workspace_id : Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id"),
        primary_key = True
    )

    user_id : Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="viewer"
    )