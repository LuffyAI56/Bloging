"""
JWT generation and verification module.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from typing import Optional
from jose import JWTError, jwt

from .config import get_settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Creates a JWT access token for authentication.
    """
    settings = get_settings()
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Creates a JWT refresh token for obtaining new access tokens.
    Returns the encoded token, its unique JTI (JWT ID), and the expiration date.
    """
    settings = get_settings()
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        
    jti = str(uuid4())
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    encoded_token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return encoded_token, jti, expire


def verify_token(token: str, token_type: str = "access"):
    """
    Verifies a JWT token and ensures its type matches the expected type.
    Returns the decoded payload if valid, None otherwise.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("sub") is None:
            raise JWTError("Invalid token: Subject missing")
        if payload.get("type") != token_type:
            raise JWTError(f"Invalid token type: Expected {token_type}")
        return payload
    except JWTError:
        return None
