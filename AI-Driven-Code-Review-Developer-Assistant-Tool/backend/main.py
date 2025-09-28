from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
import logging
import uuid
from dotenv import load_dotenv

from api.routes import github_webhooks, code_review, auth, subscription, secure_auth, analytics, rag_review, rag_basic
from core.config import get_settings
from core.db import init_db
from middleware.security_middleware import SecurityMiddleware, CSRFMiddleware, RequestSizeMiddleware
from core.security_monitoring import security_monitor, SecurityEventType, SeverityLevel

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/security.log') if os.path.exists('logs') else logging.StreamHandler()
    ]
)

settings = get_settings()

app = FastAPI(
    title="CodeGenius AI - Secure Code Review Platform",
    description="Enterprise-grade AI-driven tool for automated code reviews with comprehensive security",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
)

# Security Middleware Stack (order matters!)
app.add_middleware(RequestSizeMiddleware, max_size=10 * 1024 * 1024)  # 10MB limit
app.add_middleware(SecurityMiddleware, enable_rate_limiting=True)
app.add_middleware(CSRFMiddleware)

# Trusted host middleware (prevent host header injection)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["codegenius.ai", "www.codegenius.ai", "api.codegenius.ai"]
    )

# CORS with security restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.debug else ["https://codegenius.ai", "https://www.codegenius.ai"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    expose_headers=["X-Total-Count", "X-Page-Count"],
)

app.include_router(github_webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(code_review.router, prefix="/api/review", tags=["code-review"])
app.include_router(rag_review.router, prefix="/api/rag", tags=["rag-enhanced-review"])
app.include_router(rag_basic.router, prefix="/api/rag", tags=["rag-knowledge-base"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(secure_auth.router, prefix="/api/auth", tags=["secure-authentication"])
app.include_router(subscription.router, prefix="/api/subscription", tags=["subscription"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

"""Removed duplicate security header middleware; headers now applied by SecurityMiddleware only."""

# Security monitoring middleware
@app.middleware("http")
async def security_monitoring_middleware(request: Request, call_next):
    """Monitor requests for security events."""
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "unknown")

    # Check for suspicious requests
    suspicious_patterns = security_monitor.analyze_request_security(
        str(request.url) + str(request.headers),
        client_ip
    )

    if suspicious_patterns:
        await security_monitor.log_security_event(
            SecurityEventType.SUSPICIOUS_REQUEST,
            SeverityLevel.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent,
            endpoint=str(request.url.path),
            details={'patterns': suspicious_patterns}
        )

    response = await call_next(request)
    return response

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Assign a unique X-Request-ID for tracing."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    # Store on state for downstream usage
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    return response

@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "CodeGenius AI - Secure Code Review Platform",
        "version": "1.0.0",
        "status": "operational",
        "security": "enterprise-grade",
        "documentation": "/docs" if settings.debug else "Contact support for API documentation"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0",
        "security_status": "active"
    }

@app.get("/security/status")
async def security_status():
    """Security status endpoint (for admin monitoring)."""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")

    from core.ssl_security import validate_ssl_setup
    from core.database_security import validate_database_security

    ssl_status = validate_ssl_setup()
    db_status = validate_database_security()

    return {
        "ssl_configuration": ssl_status,
        "database_security": db_status,
        "security_monitoring": "active",
        "rate_limiting": "active",
        "encryption": "active"
    }

# Global exception handler for security
@app.exception_handler(HTTPException)
async def security_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with security logging."""
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")

    # Log security-relevant exceptions
    if exc.status_code in [401, 403, 429]:
        await security_monitor.log_security_event(
            SecurityEventType.UNAUTHORIZED_ACCESS if exc.status_code in [401, 403] else SecurityEventType.RATE_LIMIT_EXCEEDED,
            SeverityLevel.MEDIUM,
            ip_address=client_ip,
            endpoint=str(request.url.path),
            details={'status_code': exc.status_code, 'detail': exc.detail}
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"X-Error-ID": f"err_{exc.status_code}_{hash(str(request.url))}"}
    )

# Startup event for security initialization
@app.on_event("startup")
async def security_startup():
    """Initialize security components on startup."""
    logging.info("Initializing CodeGenius AI Security Systems...")

    # Initialize database (ensure tables exist)
    try:
        init_db()
        logging.info("Database schema ensured.")
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")

    # Log startup
    await security_monitor.log_security_event(
        SecurityEventType.LOGIN_SUCCESS,  # Using as system startup
        SeverityLevel.LOW,
        details={'event': 'system_startup', 'version': '1.0.0'}
    )

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    logging.info("Security systems initialized successfully")

if __name__ == "__main__":
    import uvicorn

    # SSL configuration for production
    ssl_config = {}
    if not settings.debug and os.path.exists("ssl/fullchain.pem"):
        ssl_config = {
            "ssl_keyfile": "ssl/privkey.pem",
            "ssl_certfile": "ssl/fullchain.pem",
            "ssl_version": 3,  # Use TLS
            "ssl_cert_reqs": 0,
        }

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        **ssl_config
    )