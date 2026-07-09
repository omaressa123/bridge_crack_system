import os
import jwt
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "393156804705-v60ojlk1pc0cono9crvn56bjumf6sffv.apps.googleusercontent.com")
JWT_SECRET = os.getenv("JWT_SECRET", "bridge-crack-detection-secret-key-xyz")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

security = HTTPBearer()

def verify_google_token(token: str) -> dict | None:
    """
    Verifies a Google ID token (credential) sent from the frontend.
    Returns the parsed user info dictionary if valid, else None.
    """
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        return idinfo
    except ValueError as e:
        print(f"Google ID Token verification failed: {str(e)}")
        return None

def create_jwt_token(user_id: int, email: str, name: str, picture: str) -> str:
    """
    Creates a project-specific JWT signed with our JWT_SECRET.
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "picture": picture,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict | None:
    """
    Verifies a project-specific JWT.
    Returns the decoded payload dictionary if valid, else None.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        print(f"JWT validation failed: {str(e)}")
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency to secure HTTP endpoints.
    Verifies the Authorization Bearer JWT.
    """
    token = credentials.credentials
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
