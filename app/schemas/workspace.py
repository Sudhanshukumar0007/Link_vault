from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Annotated

class WorkspaceCreate(BaseModel):
    name: Annotated[str, Field(..., min_length=3, max_length=100)]

class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    owner_id: UUID
    plan: str
    created_at: datetime

class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    workspace_id: UUID
    user_id: UUID
    role: str
    created_at: datetime
    user_name: str | None = None
    user_email: str | None = None

class InviteMember(BaseModel):
    email: str
    role: str = "viewer"  # owner, editor, viewer