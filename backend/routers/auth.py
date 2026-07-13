import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import create_jwt_token, is_admin_role, verify_google_token
from database import get_db
from models import User
from schemas import GoogleLoginRequest, GoogleLoginResponse

logger = logging.getLogger(__name__)

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


@router.post("/google", response_model=GoogleLoginResponse)
async def google_auth(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    idinfo = verify_google_token(request.credential)
    if not idinfo:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    email = idinfo.get("email")
    name = idinfo.get("name")
    picture = idinfo.get("picture")
    google_sub = idinfo.get("sub")

    if not email or not google_sub:
        raise HTTPException(status_code=400, detail="Invalid Google user profile data")

    user = db.query(User).filter(User.google_id == google_sub).first()
    if not user:
        role = "Admin" if email.lower() == ADMIN_EMAIL and ADMIN_EMAIL else "Bridge Engineer"
        user = User(
            google_id=google_sub,
            full_name=name or "",
            email=email,
            profile_picture=picture,
            role=role,
            last_login=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")
        if ADMIN_EMAIL and email.lower() == ADMIN_EMAIL:
            user.role = "Admin"
        elif is_admin_role(user.role):
            user.role = "Admin"
        user.full_name = name or user.full_name
        user.profile_picture = picture
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_jwt_token(
        user.id,
        email,
        name or user.full_name,
        picture or user.profile_picture or "",
        role=user.role,
    )

    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "picture": user.profile_picture,
            "role": user.role,
        },
    }
