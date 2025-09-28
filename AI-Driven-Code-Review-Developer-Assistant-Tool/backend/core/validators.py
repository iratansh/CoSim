import re
import html
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator, Field
from email_validator import validate_email as email_validate, EmailNotValidError
import sqlparse
from urllib.parse import urlparse

class SecurityValidationError(Exception):
    """Custom exception for security validation failures."""
    pass

class BaseSecureModel(BaseModel):
    """Base model with built-in security validations."""

    class Config:
        # Prevent extra fields to avoid injection
        extra = "forbid"
        # Validate assignment to prevent bypassing validation
        validate_assignment = True
        # Use enum values for better security
        use_enum_values = True

class SecureUserRegistration(BaseSecureModel):
    """Secure user registration model with comprehensive validation."""

    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=12, max_length=128)
    company: Optional[str] = Field(None, max_length=100)
    github_username: Optional[str] = Field(None, max_length=39)  # GitHub username limit

    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate and sanitize full name."""
        if not v or not v.strip():
            raise ValueError('Full name is required')

        # Remove HTML and dangerous characters
        sanitized = html.escape(v.strip())

        # Check for suspicious patterns
        suspicious_patterns = [
            r'<[^>]*>',  # HTML tags
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'on\w+\s*=',  # Event handlers
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValueError('Invalid characters in full name')

        # Ensure reasonable character set (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", sanitized):
            raise ValueError('Full name contains invalid characters')

        return sanitized

    @validator('email')
    def validate_email_security(cls, v):
        """Comprehensive email validation with security checks."""
        if not v:
            raise ValueError('Email is required')

        # Basic format validation
        try:
            validated_email = email_validate(v)
            email = validated_email.email
        except EmailNotValidError:
            raise ValueError('Invalid email format')

        # Additional security checks
        if len(email) > 254:  # RFC 5321 limit
            raise ValueError('Email address too long')

        # Check for suspicious patterns
        suspicious_patterns = [
            r'[<>"\']',  # Potential injection characters
            r'\.{2,}',   # Multiple consecutive dots
            r'^\.|\.$',  # Starts or ends with dot
            r'@.*@',     # Multiple @ symbols
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, email):
                raise ValueError('Email contains invalid characters')

        # Block common malicious domains (expand this list)
        blocked_domains = [
            'tempmail.org',
            '10minutemail.com',
            'guerrillamail.com',
            'mailinator.com'
        ]

        domain = email.split('@')[1].lower()
        if domain in blocked_domains:
            raise ValueError('Email domain not allowed')

        return email.lower()

    @validator('password')
    def validate_password_security(cls, v):
        """Comprehensive password validation."""
        from core.security import validate_password_strength

        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError(f"Password security requirements not met: {', '.join(errors)}")

        return v

    @validator('github_username')
    def validate_github_username(cls, v):
        """Validate GitHub username format."""
        if v is None:
            return v

        v = v.strip()
        if not v:
            return None

        # GitHub username rules
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-])*[a-zA-Z0-9]$', v):
            raise ValueError('Invalid GitHub username format')

        if len(v) > 39:  # GitHub limit
            raise ValueError('GitHub username too long')

        return v

class SecureCodeAnalysisRequest(BaseSecureModel):
    """Secure code analysis request with sanitization."""

    code: str = Field(..., min_length=1, max_length=100000)  # 100KB limit
    language: str = Field(..., min_length=1, max_length=50)
    filename: Optional[str] = Field(None, max_length=255)
    context: Optional[str] = Field(None, max_length=10000)

    @validator('code')
    def validate_code_content(cls, v):
        """Validate and sanitize code content."""
        if not v or not v.strip():
            raise ValueError('Code content is required')

        # Check for extremely large submissions (DoS protection)
        if len(v) > 100000:  # 100KB limit
            raise ValueError('Code submission too large')

        # Check for potential SQL injection patterns in code
        sql_patterns = [
            r';\s*drop\s+table',
            r';\s*delete\s+from',
            r';\s*truncate\s+table',
            r'union\s+select',
            r'exec\s*\(',
        ]

        code_lower = v.lower()
        for pattern in sql_patterns:
            if re.search(pattern, code_lower):
                # This might be legitimate code, so warn but don't block
                pass

        return v

    @validator('language')
    def validate_language(cls, v):
        """Validate programming language."""
        v = v.strip().lower()

        allowed_languages = {
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala',
            'csharp', 'objective-c', 'dart', 'r', 'matlab', 'shell'
        }

        if v not in allowed_languages:
            raise ValueError(f'Unsupported language: {v}')

        return v

    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename for security."""
        if v is None:
            return v

        v = v.strip()
        if not v:
            return None

        # Check for path traversal attempts
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename: path traversal detected')

        # Check for dangerous extensions
        dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.scr', '.pif', '.com',
            '.dll', '.msi', '.vbs', '.ps1', '.sh'
        }

        file_ext = '.' + v.split('.')[-1].lower() if '.' in v else ''
        if file_ext in dangerous_extensions:
            raise ValueError('Dangerous file extension detected')

        # Limit filename length
        if len(v) > 255:
            raise ValueError('Filename too long')

        return v

class SecurePRAnalysisRequest(BaseSecureModel):
    """Secure PR analysis request."""

    repo_url: str = Field(..., min_length=1, max_length=500)
    pr_number: int = Field(..., ge=1, le=999999)
    access_token: Optional[str] = Field(None, max_length=255)

    @validator('repo_url')
    def validate_repo_url(cls, v):
        """Validate GitHub repository URL."""
        v = v.strip()

        # Parse URL
        try:
            parsed = urlparse(v)
        except Exception:
            raise ValueError('Invalid URL format')

        # Must be HTTPS
        if parsed.scheme != 'https':
            raise ValueError('Only HTTPS URLs are allowed')

        # Must be GitHub
        allowed_hosts = {'github.com', 'www.github.com'}
        if parsed.netloc.lower() not in allowed_hosts:
            raise ValueError('Only GitHub URLs are allowed')

        # Validate path format: /owner/repo
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) != 2:
            raise ValueError('Invalid repository URL format')

        owner, repo = path_parts
        if not re.match(r'^[a-zA-Z0-9\-_.]+$', owner) or not re.match(r'^[a-zA-Z0-9\-_.]+$', repo):
            raise ValueError('Invalid repository owner or name')

        return v

    @validator('access_token')
    def validate_access_token(cls, v):
        """Validate GitHub access token format."""
        if v is None:
            return v

        v = v.strip()
        if not v:
            return None

        # GitHub token patterns
        github_patterns = [
            r'^ghp_[a-zA-Z0-9]{36}$',  # Personal access token
            r'^gho_[a-zA-Z0-9]{36}$',  # OAuth token
            r'^ghu_[a-zA-Z0-9]{36}$',  # User token
            r'^ghs_[a-zA-Z0-9]{36}$',  # Server token
        ]

        is_valid_format = any(re.match(pattern, v) for pattern in github_patterns)
        if not is_valid_format:
            raise ValueError('Invalid GitHub token format')

        return v

class SecureSubscriptionRequest(BaseSecureModel):
    """Secure subscription request."""

    tier: str = Field(..., min_length=1, max_length=50)
    payment_method_id: str = Field(..., min_length=1, max_length=255)

    @validator('tier')
    def validate_tier(cls, v):
        """Validate subscription tier."""
        v = v.strip().lower()

        allowed_tiers = {'free', 'professional', 'enterprise'}
        if v not in allowed_tiers:
            raise ValueError(f'Invalid subscription tier: {v}')

        return v

    @validator('payment_method_id')
    def validate_payment_method(cls, v):
        """Validate Stripe payment method ID format."""
        v = v.strip()

        # Stripe payment method ID format
        if not re.match(r'^pm_[a-zA-Z0-9]{24}$', v):
            raise ValueError('Invalid payment method ID format')

        return v

def sanitize_sql_input(value: str) -> str:
    """Sanitize input that might be used in SQL queries."""
    if not value:
        return value

    # Use sqlparse to detect and sanitize SQL injection attempts
    try:
        parsed = sqlparse.parse(value)
        for statement in parsed:
            # Check for dangerous SQL keywords
            dangerous_keywords = [
                'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE',
                'INSERT', 'UPDATE', 'EXEC', 'EXECUTE', 'UNION'
            ]

            for token in statement.flatten():
                if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in dangerous_keywords:
                    raise SecurityValidationError(f"Dangerous SQL keyword detected: {token.value}")

    except Exception:
        # If parsing fails, be conservative
        dangerous_patterns = [
            r';\s*(drop|delete|truncate|alter|create)',
            r'union\s+select',
            r'exec\s*\(',
            r'--\s*',
            r'/\*.*\*/',
        ]

        value_lower = value.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, value_lower):
                raise SecurityValidationError("Potential SQL injection detected")

    return html.escape(value)

def validate_file_upload(file_content: bytes, allowed_types: List[str] = None) -> bool:
    """Validate uploaded file content for security."""
    if allowed_types is None:
        allowed_types = ['text/plain', 'application/json']

    # Check file size (max 10MB)
    if len(file_content) > 10 * 1024 * 1024:
        raise SecurityValidationError("File too large")

    # Check for malicious content patterns
    malicious_patterns = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'data:text/html',
        b'<?php',
        b'<%',
    ]

    content_lower = file_content.lower()
    for pattern in malicious_patterns:
        if pattern in content_lower:
            raise SecurityValidationError("Malicious content detected in file")

    return True

def rate_limit_key(request_type: str, identifier: str) -> str:
    """Generate rate limiting key."""
    return f"rate_limit:{request_type}:{identifier}"

class IPWhitelist:
    """IP whitelist for enhanced security."""

    def __init__(self):
        # Add your trusted IP ranges here
        self.whitelist = {
            '127.0.0.1',  # Localhost
            '::1',        # IPv6 localhost
        }

    def is_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted."""
        return ip in self.whitelist

    def add_ip(self, ip: str):
        """Add IP to whitelist."""
        self.whitelist.add(ip)

    def remove_ip(self, ip: str):
        """Remove IP from whitelist."""
        self.whitelist.discard(ip)