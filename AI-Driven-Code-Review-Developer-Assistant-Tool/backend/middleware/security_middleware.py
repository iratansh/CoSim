import time
import json
import logging
from typing import Callable, Dict, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis
from datetime import datetime, timedelta
import hashlib
import asyncio

from core.config import get_settings
from core.security import get_client_ip, SECURITY_HEADERS, verify_token

settings = get_settings()
logger = logging.getLogger(__name__)

# Redis connection for rate limiting (fallback to in-memory for development)
try:
    redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()
    USE_REDIS = True
except:
    USE_REDIS = False
    in_memory_store = {}

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""

    def __init__(self, app, enable_rate_limiting: bool = True):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.blocked_ips = set()
        self.suspicious_requests = {}

        # Rate limiting configurations
        self.rate_limits = {
            'login': {'requests': 5, 'window': 900},      # 5 attempts per 15 minutes
            'register': {'requests': 3, 'window': 3600},   # 3 registrations per hour
            'api': {'requests': 1000, 'window': 3600},     # 1000 API calls per hour
            'payment': {'requests': 10, 'window': 3600},   # 10 payment attempts per hour
            'global': {'requests': 10000, 'window': 3600}, # Global rate limit
        }

        # Suspicious patterns that indicate potential attacks
        self.attack_patterns = [
            # XSS patterns
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'expression\s*\(',

            # SQL injection patterns
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'\'\s*or\s*\d+=\d+',
            r'\'\s*or\s*\'[^\']*\'\s*=\s*\'[^\']*\'',

            # Path traversal
            r'\.\./|\.\.\%2f',
            r'%2e%2e%2f',

            # Command injection
            r';\s*cat\s+',
            r';\s*ls\s+',
            r';\s*id\s*;',
            r'`[^`]*`',

            # File inclusion
            r'file:///',
            r'php://input',
            r'data://text',
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main security middleware dispatch."""
        start_time = time.time()
        client_ip = get_client_ip(request)

        try:
            # 1. Check if IP is blocked
            if self._is_ip_blocked(client_ip):
                logger.warning(f"Blocked IP {client_ip} attempted access")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Access denied"}
                )

            # 2. Check for suspicious requests
            if self._is_suspicious_request(request):
                logger.warning(f"Suspicious request from {client_ip}: {request.url}")
                self._record_suspicious_activity(client_ip)
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Bad request"}
                )

            # 3. Rate limiting
            if self.enable_rate_limiting:
                rate_limit_result = await self._check_rate_limit(request, client_ip)
                if rate_limit_result:
                    return rate_limit_result

            # 4. Process request
            response = await call_next(request)

            # 5. Add security headers
            self._add_security_headers(response)

            # 6. Log request
            self._log_request(request, response, client_ip, time.time() - start_time)

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            # Don't expose internal errors
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP address is blocked."""
        return ip in self.blocked_ips

    def _is_suspicious_request(self, request: Request) -> bool:
        """Detect suspicious request patterns."""
        import re

        # Check URL for suspicious patterns
        url_str = str(request.url)
        for pattern in self.attack_patterns:
            if re.search(pattern, url_str, re.IGNORECASE):
                return True

        # Check headers for suspicious content
        suspicious_headers = ['user-agent', 'referer', 'x-forwarded-for']
        for header_name in suspicious_headers:
            header_value = request.headers.get(header_name, '')
            for pattern in self.attack_patterns:
                if re.search(pattern, header_value, re.IGNORECASE):
                    return True

        # Check for unusual request methods
        if request.method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']:
            return True

        # Check for oversized headers
        total_header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if total_header_size > 8192:  # 8KB limit
            return True

        return False

    async def _check_rate_limit(self, request: Request, client_ip: str) -> Optional[Response]:
        """Check and enforce rate limits."""
        # Determine rate limit type based on endpoint
        path = request.url.path
        rate_type = 'api'  # default

        if '/auth/login' in path:
            rate_type = 'login'
        elif '/auth/register' in path or '/signup' in path:
            rate_type = 'register'
        elif '/subscription' in path or '/payment' in path:
            rate_type = 'payment'

        # Determine user key if authenticated
        user_key = None
        auth_header = request.headers.get('Authorization') or request.headers.get('authorization')
        if auth_header and auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ',1)[1].strip()
            payload = verify_token(token)
            if payload and payload.get('sub'):
                user_key = payload['sub']

        # Compose keys (prefer user key when present)
        identity_key = user_key or client_ip

        # Check specific rate limit (user or IP)
        if not await self._check_rate_limit_for_type(identity_key, rate_type):
            logger.warning(f"Rate limit exceeded for {client_ip} on {rate_type}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": self.rate_limits[rate_type]['window']
                },
                headers={"Retry-After": str(self.rate_limits[rate_type]['window'])}
            )

        # Check global rate limit
        if not await self._check_rate_limit_for_type(identity_key, 'global'):
            logger.warning(f"Global rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Global rate limit exceeded"},
                headers={"Retry-After": "3600"}
            )

        return None

    async def _check_rate_limit_for_type(self, client_ip: str, rate_type: str) -> bool:
        """Check rate limit for specific type."""
        if rate_type not in self.rate_limits:
            return True

        config = self.rate_limits[rate_type]
        key = f"rate_limit:{rate_type}:{client_ip}"

        if USE_REDIS:
            return await self._redis_rate_limit(key, config['requests'], config['window'])
        else:
            return self._memory_rate_limit(key, config['requests'], config['window'])

    async def _redis_rate_limit(self, key: str, max_requests: int, window: int) -> bool:
        """Redis-based rate limiting."""
        try:
            current_requests = await asyncio.get_event_loop().run_in_executor(
                None, redis_client.get, key
            )

            if current_requests is None:
                # First request
                await asyncio.get_event_loop().run_in_executor(
                    None, redis_client.setex, key, window, 1
                )
                return True
            else:
                current_requests = int(current_requests)
                if current_requests >= max_requests:
                    return False
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None, redis_client.incr, key
                    )
                    return True
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            return True  # Fail open

    def _memory_rate_limit(self, key: str, max_requests: int, window: int) -> bool:
        """In-memory rate limiting (for development)."""
        now = time.time()

        if key not in in_memory_store:
            in_memory_store[key] = {'count': 1, 'window_start': now}
            return True

        data = in_memory_store[key]

        # Check if window has expired
        if now - data['window_start'] >= window:
            data['count'] = 1
            data['window_start'] = now
            return True

        # Check if limit exceeded
        if data['count'] >= max_requests:
            return False

        data['count'] += 1
        return True

    def _record_suspicious_activity(self, client_ip: str):
        """Record suspicious activity and auto-block if necessary."""
        now = time.time()

        if client_ip not in self.suspicious_requests:
            self.suspicious_requests[client_ip] = []

        self.suspicious_requests[client_ip].append(now)

        # Remove old entries (older than 1 hour)
        self.suspicious_requests[client_ip] = [
            timestamp for timestamp in self.suspicious_requests[client_ip]
            if now - timestamp < 3600
        ]

        # Auto-block if too many suspicious requests
        if len(self.suspicious_requests[client_ip]) >= 5:
            self.blocked_ips.add(client_ip)
            logger.warning(f"Auto-blocked IP {client_ip} due to suspicious activity")

    def _add_security_headers(self, response: Response):
        """Add security headers to response."""
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

    def _log_request(self, request: Request, response: Response, client_ip: str, duration: float):
        """Log request for security monitoring."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': client_ip,
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration': round(duration, 3),
            'user_agent': request.headers.get('user-agent', ''),
            'referer': request.headers.get('referer', ''),
        }

        # Log to security log
        if response.status_code >= 400:
            logger.warning(f"HTTP {response.status_code}: {json.dumps(log_data)}")
        else:
            logger.info(f"Request: {json.dumps(log_data)}")

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.safe_methods = {'GET', 'HEAD', 'OPTIONS', 'TRACE'}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """CSRF protection dispatch."""
        # Skip CSRF for safe methods
        if request.method in self.safe_methods:
            return await call_next(request)

        # Skip CSRF for API endpoints with proper authentication
        if request.url.path.startswith('/api/') and 'authorization' in request.headers:
            return await call_next(request)

        # Check CSRF token for state-changing requests
        csrf_token = request.headers.get('X-CSRF-Token')
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing"}
            )

        # Validate CSRF token (implement your CSRF validation logic)
        if not self._validate_csrf_token(csrf_token, request):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token"}
            )

        return await call_next(request)

    def _validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token."""
        # Implement your CSRF token validation logic here
        # This is a simplified version - use proper CSRF libraries in production
        return len(token) >= 32  # Basic length check

class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request size."""

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check request size."""
        content_length = request.headers.get('content-length')

        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request too large"}
                )

        return await call_next(request)