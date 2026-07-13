import os
import jwt
import logging
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

if not GOOGLE_CLIENT_ID:
    logger.warning("GOOGLE_CLIENT_ID is not set — Google login will fail")
if not JWT_SECRET:
    logger.warning("JWT_SECRET is not set — JWT operations will fail")

security = HTTPBearer()


def is_admin_role(role: str | None) -> bool:
    """True for ADMIN and legacy Admin values."""
    return bool(role and role.strip().upper() == "ADMIN")


def verify_google_token(token: str) -> dict | None:
    """Verify a Google ID token sent from the frontend."""
    if not GOOGLE_CLIENT_ID:
        return None
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        return idinfo
    except ValueError as e:
        logger.warning("Google ID token verification failed: %s", e)
        return None


def create_jwt_token(user_id: int, email: str, name: str, picture: str, role: str | None = None) -> str:
    """Create a project-specific JWT signed with JWT_SECRET."""
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "picture": picture,
        "role": role or "Bridge Engineer",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict | None:
    """Verify a project-specific JWT."""
    if not JWT_SECRET:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        logger.warning("JWT validation failed: %s", e)
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency to secure HTTP endpoints."""
    token = credentials.credentials
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require Admin role for protected admin endpoints."""
    if not is_admin_role(current_user.get("role")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
