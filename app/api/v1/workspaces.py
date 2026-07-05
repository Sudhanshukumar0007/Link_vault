from fastapi import APIRouter, Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.session import get_db
from sqlalchemy import select 
from app.api.deps import get_current_user
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceMemberResponse, InviteMember
from sqlalchemy.orm import joinedload
from app.services.workspace_service import (
    create_workspace, get_user_workspaces, get_workspace,
    invite_member, remove_member
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.post("/", response_model=WorkspaceResponse)
async def create(
    data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await create_workspace(db, data, current_user.id)

@router.get("/", response_model=list[WorkspaceResponse])
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_user_workspaces(db, current_user.id)

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_workspace(db, workspace_id, current_user.id)

@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse)
async def invite(
    workspace_id: UUID,
    data: InviteMember,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await invite_member(db, workspace_id, data.email, data.role, current_user.id)

@router.delete("/{workspace_id}/members/{user_id}")
async def remove(
    workspace_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await remove_member(db, workspace_id, user_id, current_user.id)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_members(
    workspace_id: UUID,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await get_workspace(db, workspace_id, current_user.id)

    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()

    return [
        WorkspaceMemberResponse(
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role,
            created_at=member.created_at,
            user_name=user.name,
            user_email=user.email
        )
        for member, user in rows
    ]