"""
API routes for authentications.
"""
from datetime import datetime, timezone
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import database, hashing, models, schemas, token as auth_token

router = APIRouter(tags=["Authentication"])


invalid_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def hash_token(value: str):
    """Handles hash token logic."""
    return sha256(value.encode("utf-8")).hexdigest()


def utc_now_naive():
    """Handles utc now naive logic."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_token_pair(user: models.User, db: Session):
    """Handles create token pair logic."""
    access_token = auth_token.create_access_token(data={"sub": user.email})
    refresh_token, jti, expires_at = auth_token.create_refresh_token(data={"sub": user.email})

    db.add(
        models.RefreshToken(
            jti=jti,
            token_hash=hash_token(refresh_token),
            user_id=user.id,
            expires_at=expires_at,
        )
    )
    db.commit()

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    email = request.username.strip().lower()
    user = db.query(models.User).filter(models.User.email == email, models.User.is_active == True).first()

    if not user:
        raise invalid_credentials_exception

    if not hashing.PasswordHasher.verify_password(request.password, user.password):
        raise invalid_credentials_exception

    return create_token_pair(user, db)


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(request: schemas.RefreshTokenRequest, db: Session = Depends(database.get_db)):
    payload = auth_token.verify_token(request.refresh_token, token_type="refresh")
    if payload is None:
        raise invalid_credentials_exception

    token_record = db.query(models.RefreshToken).filter(
        models.RefreshToken.jti == payload.get("jti"),
        models.RefreshToken.token_hash == hash_token(request.refresh_token),
        models.RefreshToken.revoked_at.is_(None),
    ).first()

    if not token_record or token_record.expires_at < utc_now_naive():
        raise invalid_credentials_exception

    user = db.query(models.User).filter(models.User.email == payload["sub"], models.User.is_active == True).first()
    if not user:
        raise invalid_credentials_exception

    token_record.revoked_at = utc_now_naive()
    db.commit()
    return create_token_pair(user, db)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: schemas.LogoutRequest, db: Session = Depends(database.get_db)):
    payload = auth_token.verify_token(request.refresh_token, token_type="refresh")
    if payload is None:
        return None

    token_record = db.query(models.RefreshToken).filter(
        models.RefreshToken.jti == payload.get("jti"),
        models.RefreshToken.token_hash == hash_token(request.refresh_token),
        models.RefreshToken.revoked_at.is_(None),
    ).first()

    if token_record:
        token_record.revoked_at = utc_now_naive()
        db.commit()

    return None
