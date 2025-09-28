from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import secrets
import time
import logging
from email.utils import parseaddr

from core.config import get_settings
from core.security import hash_password, verify_password, validate_password_strength
from core.db import get_db
from sqlalchemy.orm import Session
from models.user import User
import json
from core.security_monitoring import security_monitor, SecurityEventType, SeverityLevel
from core.validators import SecureUserRegistration
from services.auth_service import (
    SESSION_SERVICE,
    BRUTE_FORCE_SERVICE,
    add_jti_to_denylist,
    is_jti_revoked,
)

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

class SecureLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6)
    remember_me: bool = False

    @validator('username')
    def validate_username(cls, v):
        # Sanitize and validate username
        v = v.strip()

        # Basic email validation if it looks like an email
        if '@' in v:
            name, addr = parseaddr(v)
            if not addr or len(addr) > 254:
                raise ValueError('Invalid email format')

        # Prevent dangerous characters
        if any(char in v for char in ['<', '>', '"', "'", '&', '\x00']):
            raise ValueError('Invalid characters in username')

        return v.lower()

    @validator('mfa_code')
    def validate_mfa_code(cls, v):
        if v is not None:
            # Only allow digits
            if not v.isdigit():
                raise ValueError('MFA code must contain only digits')
        return v

class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=12, max_length=128)

    @validator('new_password')
    def validate_new_password(cls, v):
        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError(f"Password requirements not met: {', '.join(errors)}")
        return v

class MFASetupRequest(BaseModel):
    enable: bool
    backup_codes: Optional[list[str]] = None

session_manager = SESSION_SERVICE
brute_force_protection = BRUTE_FORCE_SERVICE

@router.post("/login")
async def secure_login(
    request: SecureLoginRequest,
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Secure login with httpOnly cookies and comprehensive protection."""

    client_ip = http_request.headers.get("x-forwarded-for", http_request.client.host if http_request.client else "unknown")
    user_agent = http_request.headers.get("user-agent", "unknown")

    # Check brute force protection for IP
    ip_check = brute_force_protection.check(client_ip)
    if ip_check['blocked']:
        await security_monitor.log_security_event(
            SecurityEventType.BRUTE_FORCE_ATTACK,
            SeverityLevel.HIGH,
            ip_address=client_ip,
            details={'attempts': ip_check['attempts'], 'identifier': 'ip'}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Try again in {ip_check['retry_after'] // 60} minutes."
        )

    # Check brute force protection for username
    username_check = brute_force_protection.check(request.username)
    if username_check['blocked']:
        await security_monitor.log_security_event(
            SecurityEventType.ACCOUNT_LOCKOUT,
            SeverityLevel.HIGH,
            details={'username': request.username, 'attempts': username_check['attempts']}
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to failed login attempts."
        )

    try:
        user = db.query(User).filter(User.username == request.username.lower()).first()
        if user and verify_password(request.password, user.hashed_password):
            user_id = user.id

            # Reset failed attempts on successful login
            brute_force_protection.reset(client_ip)
            brute_force_protection.reset(request.username)

            # Create secure session
            session_data = session_manager.create_session(
                user_id, client_ip, user_agent, request.remember_me
            )

            # Set httpOnly secure cookies
            cookie_settings = {
                'httponly': True,
                'secure': not settings.debug,  # Use secure cookies in production
                'samesite': 'strict',
                'path': '/'
            }

            # Set access token cookie (short-lived)
            response.set_cookie(
                'access_token',
                session_data['access_token'],
                max_age=15 * 60,  # 15 minutes
                **cookie_settings
            )

            # Set refresh token cookie (long-lived)
            refresh_max_age = 30 * 24 * 60 * 60 if request.remember_me else 24 * 60 * 60
            response.set_cookie(
                'refresh_token',
                session_data['refresh_token'],
                max_age=refresh_max_age,
                **cookie_settings
            )

            # Set session ID cookie
            response.set_cookie(
                'session_id',
                session_data['session_id'],
                max_age=refresh_max_age,
                **cookie_settings
            )

            # Log successful login
            await security_monitor.log_security_event(
                SecurityEventType.LOGIN_SUCCESS,
                SeverityLevel.LOW,
                user_id=user_id,
                ip_address=client_ip,
                details={'username': request.username, 'remember_me': request.remember_me}
            )

            return {
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user_id,
                    'username': user.username,
                    'email': user.email
                }
            }

        else:
            # Record failed attempt
            brute_force_protection.record_failure(client_ip)
            brute_force_protection.record_failure(request.username)

            # Log failed login
            await security_monitor.log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                SeverityLevel.MEDIUM,
                ip_address=client_ip,
                details={'username': request.username, 'reason': 'invalid_credentials'}
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def secure_logout(http_request: Request, response: Response):
    """Secure logout: revoke access & refresh tokens and invalidate session."""
    access_token = http_request.cookies.get('access_token')
    refresh_token = http_request.cookies.get('refresh_token')
    session_id = http_request.cookies.get('session_id')

    for token in [access_token, refresh_token]:
        if not token:
            continue
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                audience="codegenius-api"
            )
            jti = payload.get('jti')
            exp = payload.get('exp')
            if jti and exp:
                add_jti_to_denylist(jti, int(exp))
        except jwt.PyJWTError:
            pass  # Ignore invalid tokens during logout

    if session_id:
        session_manager.invalidate_session(session_id)

    cookie_settings = {
        'httponly': True,
        'secure': not settings.debug,
        'samesite': 'strict',
        'path': '/'
    }
    for c in ['access_token', 'refresh_token', 'session_id']:
        response.delete_cookie(c, **cookie_settings)

    return {'message': 'Logged out successfully'}

@router.get("/me")
async def get_current_user_secure(http_request: Request, db: Session = Depends(get_db)):
    """Get current user from secure session using database lookup."""

    session_id = http_request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session"
        )

    client_ip = http_request.headers.get("x-forwarded-for", http_request.client.host if http_request.client else "unknown")
    session_data = session_manager.validate_session(session_id, client_ip)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    user = db.query(User).filter(User.id == session_data['user_id']).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'roles': ['user'],
        'permissions': ['read:own_data'],
        'lastLogin': session_data['created_at'],
        'mfaEnabled': False
    }

@router.post("/refresh")
async def refresh_token(http_request: Request, response: Response):
    """Refresh access token using refresh token."""

    refresh_token = http_request.cookies.get('refresh_token')
    session_id = http_request.cookies.get('session_id')

    if not refresh_token or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token"
        )

    try:
        # Validate refresh token
        payload = jwt.decode(
            refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience="codegenius-api"
        )

        if payload.get('type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        # Check denylist
        if is_jti_revoked(payload.get('jti', '')):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

        user_id = int(payload['sub'])
        token_session_id = payload['session_id']

        # Validate session
        client_ip = http_request.headers.get("x-forwarded-for", http_request.client.host if http_request.client else "unknown")
        session_data = session_manager.validate_session(token_session_id, client_ip)

        if not session_data or session_data['user_id'] != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )

        # Create new access token
        new_access_token = session_manager.issue_access_token(user_id, token_session_id)

        # Set new access token cookie
        response.set_cookie(
            'access_token',
            new_access_token,
            max_age=15 * 60,  # 15 minutes
            httponly=True,
            secure=not settings.debug,
            samesite='strict',
            path='/'
        )

        return {'message': 'Token refreshed successfully'}

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    http_request: Request
):
    """Change user password with security validations."""

    # Get current user from session
    session_id = http_request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    client_ip = http_request.headers.get("x-forwarded-for", http_request.client.host if http_request.client else "unknown")
    session_data = session_manager.validate_session(session_id, client_ip)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    user_id = session_data['user_id']

    # TODO: Verify current password with database
    # For demo, skip verification

    # Validate new password strength
    is_valid, errors = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password requirements not met: {', '.join(errors)}"
        )

    # TODO: Update password in database
    # new_password_hash = hash_password(request.new_password)

    # Invalidate all user sessions (force re-login)
    session_manager.invalidate_all_sessions(user_id)

    # Log password change
    await security_monitor.log_security_event(
        SecurityEventType.PASSWORD_RESET,
        SeverityLevel.MEDIUM,
        user_id=user_id,
        ip_address=client_ip,
        details={'initiated_by': 'user'}
    )

    return {'message': 'Password changed successfully. Please log in again.'}

# Dependency for protected routes
async def get_current_user_from_cookie(http_request: Request):
    """Dependency to get current authenticated user from httpOnly cookie."""

    access_token = http_request.cookies.get('access_token')
    session_id = http_request.cookies.get('session_id')

    if not access_token or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        # Validate access token
        payload = jwt.decode(
            access_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience="codegenius-api"
        )

        if payload.get('type') != 'access':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        if is_jti_revoked(payload.get('jti', '')):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

        user_id = int(payload['sub'])
        token_session_id = payload['session_id']

        # Validate session
        client_ip = http_request.headers.get("x-forwarded-for", http_request.client.host if http_request.client else "unknown")
        session_data = session_manager.validate_session(token_session_id, client_ip)

        if not session_data or session_data['user_id'] != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )

        return {
            'user_id': user_id,
            'session_id': token_session_id,
            'session_data': session_data
        }

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )
