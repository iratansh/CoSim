from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from core.config import get_settings
from core.security import hash_password, verify_password, validate_password_strength
from core.db import get_db
from models.user import User, SubscriptionTier
from core.tokens import (
    generate_email_verification_token,
    verify_email_token,
    generate_password_reset_token,
    verify_password_reset_token,
)

router = APIRouter()
security = HTTPBearer()

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    full_name: Optional[str] = None
    company: Optional[str] = None

class RegistrationResponse(BaseModel):
    id: int
    username: str
    email: str
    subscription_tier: str
    email_verification_token: Optional[str] = None
    email_verified: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@router.post("/register", response_model=RegistrationResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user with password strength validation."""
    # Check existing username/email
    existing = db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    is_valid, errors = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Password requirements not met: {', '.join(errors)}")

    user = User(
        username=user_data.username.lower(),
        email=user_data.email.lower(),
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        company=user_data.company,
        subscription_tier=SubscriptionTier.FREE
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate one-time email verification token (return for now; production would email it)
    verification_token = generate_email_verification_token(user.id, user.email)
    return RegistrationResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        subscription_tier=user.subscription_tier.value,
        email_verification_token=verification_token,
        email_verified=bool(user.email_verified_at)
    )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token from DB-backed credentials."""
    settings = get_settings()

    user = db.query(User).filter(User.username == user_data.username.lower()).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_data = {
        "sub": user.username,
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    }
    token = jwt.encode(token_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return {"access_token": token, "token_type": "bearer"}

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract and validate JWT token."""
    settings = get_settings()

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information from database."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email
    )

class EmailVerificationRequest(BaseModel):
    token: str

@router.post("/verify-email")
async def verify_email(payload: EmailVerificationRequest, db: Session = Depends(get_db)):
    data = verify_email_token(payload.token)
    if not data:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == data["sub"], User.email == data["email"].lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email_verified_at:
        return {"message": "Email already verified"}
    user.email_verified_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(request: Request, db: Session = Depends(get_db)):
    # Use bearer token to authenticate current user
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = auth_header.split(" ", 1)[1].strip()
    from core.security import verify_token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email_verified_at:
        return {"message": "Email already verified"}
    new_token = generate_email_verification_token(user.id, user.email)
    return {"verification_token": new_token}

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetTokenPayload(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12, max_length=128)

@router.post("/request-password-reset")
async def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    # Always respond success (avoid user enumeration) but only generate token if user exists
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user:
        reset_token = generate_password_reset_token(user.id, user.email)
        # For now return in response; production would email this
        return {"message": "If the account exists, a reset token has been generated.", "reset_token": reset_token}
    return {"message": "If the account exists, a reset token has been generated."}

@router.post("/reset-password")
async def reset_password(payload: PasswordResetTokenPayload, db: Session = Depends(get_db)):
    data = verify_password_reset_token(payload.token)
    if not data:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == data['sub'], User.email == data['email'].lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    is_valid, errors = validate_password_strength(payload.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Password requirements not met: {', '.join(errors)}")
    user.hashed_password = hash_password(payload.new_password)
    user.password_changed_at = datetime.utcnow()
    db.commit()
    return {"message": "Password reset successful"}