from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import (
    hash_pwd, verify_pwd, create_access_token,
    generate_refresh_token,hash_refresh_token, create_refresh_token_expiry
    )
from app.models.refresh_token import RefreshToken
from datetime import datetime,timezone
from uuid import UUID

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_pwd(data.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, email: str, password: str) -> str:
    user = await get_user_by_email(db, email)
    if not user or not verify_pwd(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    access_token = create_access_token({"sub": str(user.id)})
    
    raw_refresh_token = generate_refresh_token()
    refresh_token_obj = RefreshToken(
        token_hash = hash_refresh_token(raw_refresh_token),
        user_id = user.id,
        expires_at = create_refresh_token_expiry()
    )
    db.add(refresh_token_obj)
    await db.commit()

    return{
        "access_token":access_token,
        "refresh_token":raw_refresh_token,
        "token_type":"bearer"
    }


async def refresh_access_token(db: AsyncSession, raw_token: str) -> dict:
    token_hash = hash_refresh_token(raw_token)
    
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False
        )
    )
    refresh_token = result.scalar_one_or_none()
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    if refresh_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")
    
    # revoke old token (rotation)
    refresh_token.is_revoked = True
    
    # issue new tokens
    new_access_token = create_access_token({"sub": str(refresh_token.user_id)})
    new_raw_refresh = generate_refresh_token()
    new_refresh_obj = RefreshToken(
        token_hash=hash_refresh_token(new_raw_refresh),
        user_id=refresh_token.user_id,
        expires_at=create_refresh_token_expiry()
    )
    db.add(new_refresh_obj)
    await db.commit()
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_raw_refresh,
        "token_type": "bearer"
    }

async def get_me(db: AsyncSession, user_id: UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()