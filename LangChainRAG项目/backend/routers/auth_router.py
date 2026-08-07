"""
Authentication router: user registration, login, profile, and password management.

All endpoints under ``/api/auth``.
- Register and Login are public (no token required).
- /me and /change-password require a valid JWT token.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserRegister, UserLogin, UserInfo, Token, ChangePassword
from auth import hash_password, verify_password, create_access_token, get_current_user
from config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new regular (non-admin) user account. Returns a JWT token
    so the user is logged in immediately after registration.

    Usernames must be unique — a 400 error is returned if the username
    is already taken.
    """
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserInfo.model_validate(user))


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate with username and password. Returns a JWT token on success.

    A generic "username or password incorrect" message is returned on failure
    to avoid revealing whether the username exists in the system.
    """
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserInfo.model_validate(user))


@router.get("/me", response_model=UserInfo)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return UserInfo.model_validate(current_user)


@router.put("/change-password")
def change_password(
    data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change the current user's password. Requires the old password for
    verification before updating to the new one.
    """
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "密码修改成功"}
