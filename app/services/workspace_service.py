from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models.workspace import Workspace, WorkspaceMember
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate,WorkspaceMemberResponse

async def create_workspace(db: AsyncSession, data: WorkspaceCreate, user_id: UUID) -> Workspace:
    workspace = Workspace(
        name=data.name,
        owner_id=user_id,
        plan="free"
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    # add creator as owner member
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user_id,
        role="owner"
    )
    db.add(member)
    await db.commit()
    return workspace

async def get_user_workspaces(db: AsyncSession, user_id: UUID) -> list[Workspace]:
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
    )
    return result.scalars().all()

async def get_workspace(db: AsyncSession, workspace_id: UUID, user_id: UUID) -> Workspace:
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(Workspace.id == workspace_id, WorkspaceMember.user_id == user_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

async def invite_member(db: AsyncSession, workspace_id: UUID, email: str, role: str, current_user_id: UUID) -> WorkspaceMember:
    # check current user is owner
    member_check = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user_id,
            WorkspaceMember.role == "owner"
        )
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Only owners can invite members")

    # find user by email
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # check not already a member
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already a member")

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return WorkspaceMemberResponse(
    workspace_id=member.workspace_id,
    user_id=member.user_id,
    role=member.role,
    created_at=member.created_at,
    user_name=user.name,
    user_email=user.email,
    )

async def remove_member(db: AsyncSession, workspace_id: UUID, user_id: UUID, current_user_id: UUID) -> dict:
    # check current user is owner
    owner_check = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user_id,
            WorkspaceMember.role == "owner"
        )
    )
    if not owner_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Only owners can remove members")

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(member)
    await db.commit()
    return {"message": "Member removed successfully"}
async def check_workspace_quota(db: AsyncSession, workspace_id: UUID) -> None:
    from app.models.link import Link
    from sqlalchemy import func
    
    workspace = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = workspace.scalar_one_or_none()
    
    if ws.plan == "free":
        count_result = await db.execute(
            select(func.count(Link.id)).where(
                Link.workspace_id == workspace_id,
                Link.is_active == True
            )
        )
        count = count_result.scalar()
        if count >= 100:
            raise HTTPException(
                status_code=403,
                detail="Free workspace limit of 100 links reached. Upgrade to pro."
            )