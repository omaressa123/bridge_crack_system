"""Shared API dependencies for authentication and resource lookup."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Bridge, User


def get_current_active_user(
    db: Session = Depends(get_db),
    token_user: dict = Depends(get_current_user),
) -> dict:
    """Validate JWT and ensure the user exists and is active in the database."""
    user_id = int(token_user["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    return {
        **token_user,
        "sub": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "role": user.role,
    }


def get_current_admin_user(
    db: Session = Depends(get_db),
    token_user: dict = Depends(get_current_user),
) -> User:
    """Require Admin role and return the database user."""
    if token_user.get("role") != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    user_id = int(token_user["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is disabled or not found",
        )
    return user


def get_bridge_or_404(bridge_id: int, db: Session = Depends(get_db)) -> Bridge:
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bridge not found")
    return bridge
