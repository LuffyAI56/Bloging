"""
OAuth2 authentication dependencies.
Provides utilities for extracting and verifying the current user from JWT tokens.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from blog import database, models, schemas
from blog.token import verify_token

# OAuth2 scheme requiring a bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Optional OAuth2 scheme that does not throw a 401 error if token is missing
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
):
    """
    Dependency that enforces authentication.
    Verifies the JWT token and fetches the current active user from the database.
    Raises 401 Unauthorized if the token is invalid or missing.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    token_user = _user_from_payload(payload, db)
    if token_user is None:
        raise credentials_exception

    return token_user


def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(database.get_db)
):
    """
    Dependency that optionally extracts the current user.
    If no token is provided, returns None.
    If a token is provided but invalid, returns None without raising an error.
    """
    if not token:
        return None

    payload = verify_token(token)
    if payload is None:
        return None

    return _user_from_payload(payload, db)


def _user_from_payload(payload: dict, db: Session):
    """
    Resolve a `schemas.TokenData` from a decoded JWT payload.
    Returns `None` if the payload is invalid or the user does not exist/active.
    """
    username: str = payload.get("sub")
    if username is None:
        return None

    user = db.query(models.User).filter(models.User.email == username, models.User.is_active == True).first()
    if user is None:
        return None

    return schemas.TokenData(email=user.email, id=user.id, role=user.role)
