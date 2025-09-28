import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import re
import bleach
from sqlalchemy.orm import Session

from core.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()

# Password requirements
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIREMENTS = {
    'uppercase': r'[A-Z]',
    'lowercase': r'[a-z]',
    'digit': r'\d',
    'special': r'[!@#$%^&*(),.?":{}|<>]'
}

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password meets security requirements."""
    errors = []

    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")

    for requirement, pattern in PASSWORD_REQUIREMENTS.items():
        if not re.search(pattern, password):
            errors.append(f"Password must contain at least one {requirement} character")

    # Check for common passwords
    common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in common_passwords:
        errors.append("Password is too common")

    return len(errors) == 0, errors

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with enhanced security."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)

    # Add security claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(32),  # JWT ID for token revocation
        "aud": "codegenius-api",  # Audience
        "iss": "codegenius.ai"   # Issuer
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token with comprehensive validation."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience="codegenius-api",
            issuer="codegenius.ai"
        )

        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            return None

        return payload

    except JWTError:
        return None

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token."""
    return secrets.token_urlsafe(length)

def constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(val1.encode('utf-8'), val2.encode('utf-8'))

def sanitize_input(input_string: str, allowed_tags: list = None) -> str:
    """Sanitize user input to prevent XSS attacks."""
    if allowed_tags is None:
        allowed_tags = []

    # Remove potentially dangerous HTML tags and attributes
    cleaned = bleach.clean(
        input_string,
        tags=allowed_tags,
        attributes={},
        strip=True
    )

    return cleaned.strip()

def validate_email(email: str) -> bool:
    """Validate email format with enhanced security checks."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        return False

    # Additional security checks
    if len(email) > 254:  # RFC 5321 limit
        return False

    local, domain = email.rsplit('@', 1)
    if len(local) > 64:  # RFC 5321 limit
        return False

    # Check for suspicious patterns
    suspicious_patterns = [
        r'\.{2,}',  # Multiple consecutive dots
        r'^\.|\.$',  # Starts or ends with dot
        r'[<>"\']',  # Potential injection characters
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, email):
            return False

    return True

def get_client_ip(request: Request) -> str:
    """Safely extract client IP address."""
    # Check for forwarded headers (behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection
    return request.client.host if request.client else "unknown"

def check_rate_limit(request: Request, max_requests: int = 100, window_minutes: int = 15) -> bool:
    """Simple in-memory rate limiting (use Redis in production)."""
    # This is a basic implementation - use Redis for production
    client_ip = get_client_ip(request)

    # In production, implement proper rate limiting with Redis
    # For now, return True (allow all requests)
    return True

class SecurityMiddleware:
    """Custom security middleware for additional protection."""

    def __init__(self):
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'eval\(',
            r'expression\(',
            r'vbscript:',
        ]

    def is_suspicious_request(self, request: Request) -> bool:
        """Check if request contains suspicious patterns."""
        # Check URL for suspicious patterns
        url = str(request.url)
        for pattern in self.suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        # Check headers for suspicious content
        for header_value in request.headers.values():
            for pattern in self.suspicious_patterns:
                if re.search(pattern, header_value, re.IGNORECASE):
                    return True

        return False

    def block_ip(self, ip: str, duration_hours: int = 24):
        """Block IP address (implement with Redis in production)."""
        self.blocked_ips.add(ip)

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        return ip in self.blocked_ips

# Dependency for protected routes
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Additional security checks
        if payload.get("aud") != "codegenius-api":
            raise credentials_exception

        return username

    except Exception:
        raise credentials_exception

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.stripe.com; "
        "frame-src https://js.stripe.com; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
}

def add_security_headers(response):
    """Add security headers to response."""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response