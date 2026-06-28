"""
app/auth.py — JWT-based API authentication.

Flow:
  1. Client sends API key to POST /token
  2. Server validates key and returns JWT
  3. Client uses JWT in Authorization: Bearer <token> header
  4. Server validates JWT on every protected endpoint

API keys are stored in .env (no database needed for this demo).
In production, use a proper secrets manager.
"""

import os
import time
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# ── Config ───────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production-please")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "1"))

# Valid API keys (comma-separated in .env)
_raw_keys = os.getenv("API_KEYS", "dev-key-123,test-key-456")
VALID_API_KEYS = set(k.strip() for k in _raw_keys.split(","))

security = HTTPBearer()


def create_access_token(api_key: str) -> str:
    """Create a JWT token for a validated API key."""
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": api_key,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def validate_api_key(api_key: str) -> bool:
    """Check if an API key is valid."""
    return api_key in VALID_API_KEYS


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency — validates JWT token from Authorization header.
    Returns the API key (subject) if valid.
    Raises 401 if invalid or expired.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        api_key: str = payload.get("sub")
        if api_key is None:
            raise credentials_exception
        return api_key
    except JWTError:
        raise credentials_exception