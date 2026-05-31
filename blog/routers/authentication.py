"""
API routes for authentications.
"""
from datetime import datetime, timezone
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import database, hashing, models, schemas, token as auth_token
from ..rate_limiter import otp_rate_limiter
from ..repository import user as user_repo
from ..repository.user import request_email_otp, verify_email_otp
from ..schemas import EmailOTPRequest, VerifyOTPRequest
from ..config import get_settings
from ..emailer import send_otp_email

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


@router.post("/register", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: schemas.CreateUserRequest, db: Session = Depends(database.get_db)):
    # Require that the email was verified via OTP. The client may submit `otp` in the registration
    # payload (one-step flow) or verify previously via `POST /verify-otp` (two-step flow).
    email = request.email
    if request.otp:
        ok = verify_email_otp(email, request.otp, db)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    else:
        # If no OTP provided, ensure there is a previously used OTP record
        if not user_repo.is_email_verified(email, db):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not verified with OTP")

    user = user_repo.create_user(request, db)
    return create_token_pair(user, db)


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


OTP_EMAIL_LIMIT = 3
OTP_EMAIL_WINDOW_SECONDS = 15 * 60
OTP_IP_LIMIT = 15
OTP_IP_WINDOW_SECONDS = 60 * 60


def get_client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@router.post("/request-otp")
def request_otp(body: EmailOTPRequest, db: Session = Depends(database.get_db), request: Request = None):
    """Generate an email OTP and return the code for dev/testing.

    In production, replace returning the code with sending it via SMTP/SES/Postmark.
    """
    client_ip = get_client_ip(request)
    if not otp_rate_limiter.allow(body.email, OTP_EMAIL_LIMIT, OTP_EMAIL_WINDOW_SECONDS):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OTP request limit exceeded for this email. Try again later.",
        )

    if not otp_rate_limiter.allow(client_ip, OTP_IP_LIMIT, OTP_IP_WINDOW_SECONDS):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OTP request limit exceeded for this IP address. Try again later.",
        )

    code = request_email_otp(body.email, db)
    settings = get_settings()
    # If configured, send via SMTP and do not return the code in the response.
    if settings.send_otp_via_email:
        try:
            send_otp_email(body.email, code)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
        return {"sent": True}

    # Default/dev behavior: return the code in the response to simplify testing.
    return {"code": code}


@router.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(database.get_db)):
    """Verify an OTP for an email address."""
    ok = verify_email_otp(request.email, request.code, db)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    return {"verified": True}
