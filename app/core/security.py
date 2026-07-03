import bcrypt
from jose import JWTError, jwt
from app.core.config import settings
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

def generate_refresh_token() -> str:
    """Generate a random refresh token string"""
    return secrets.token_urlsafe(32)

def hash_refresh_token(token: str) -> str:
    """Hash refresh token before storing in DB"""
    return hashlib.sha256(token.encode()).hexdigest()

def create_refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


def hash_pwd(pwd: str) -> str:
    pwd_bytes = pwd.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_pwd.encode('utf-8'),
            hashed_pwd.encode('utf-8')
        )
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    copy_data = data.copy()
    copy_data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(copy_data, settings.SECRET_KEY, settings.ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None