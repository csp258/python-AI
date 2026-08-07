"""
Authentication and authorization module.

Provides:
- Password hashing and verification (bcrypt via passlib)
- JWT access token creation (python-jose)
- FastAPI dependencies: ``get_current_user`` (authenticated) and ``require_admin`` (admin gate)
"""

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models import User

# bcrypt context: automatically handles salt generation and algorithm upgrades
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer extracts the Bearer token from the Authorization header
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt and return the hash string for storage."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Compare a plaintext password against a stored bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """
    Build a signed JWT with an expiration timestamp.

    The ``sub`` claim in ``data`` should contain the user ID.
    Token expiry is controlled by ``jwt_expire_minutes`` in settings.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency: extract and validate the JWT, then return the corresponding User.

    Raises 401 if the token is missing, expired, tampered with, or the user no longer exists.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency: gate that only allows admin users through.

    Must be used AFTER ``get_current_user`` has already authenticated the request.
    Raises 403 if the authenticated user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
