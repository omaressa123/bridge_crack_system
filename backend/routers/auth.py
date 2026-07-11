from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import verify_google_token, create_jwt_token
from schemas import GoogleLoginRequest

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)

@router.post("/google")
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
        user = User(
            google_id=google_sub,
            full_name=name or "",
            email=email,
            profile_picture=picture,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.full_name = name or user.full_name
        user.profile_picture = picture
        db.commit()
        db.refresh(user)

    token = create_jwt_token(user.id, email, name, picture)

    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "picture": user.profile_picture,
            "role": user.role,
        }
    }
