import os
import base64
import logging
from typing import Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import secrets

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class DatabaseSecurity:
    """Database security utilities including encryption and secure connections."""

    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data."""
        key_env = os.getenv('DATABASE_ENCRYPTION_KEY')

        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env.encode())
            except Exception as e:
                logger.error(f"Invalid encryption key in environment: {e}")

        # Generate new key if not found
        logger.warning("Generating new encryption key - ensure this is persisted!")
        return Fernet.generate_key()

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before storing in database."""
        if not data:
            return data

        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise ValueError("Failed to encrypt sensitive data")

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data from database."""
        if not encrypted_data:
            return encrypted_data

        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError("Failed to decrypt sensitive data")

    def hash_pii_for_lookup(self, pii_data: str) -> str:
        """Create searchable hash of PII data."""
        if not pii_data:
            return pii_data

        # Use PBKDF2 with salt for consistent hashing
        salt = b'codegenius_pii_salt'  # Use a consistent salt for lookups
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(pii_data.encode())
        return base64.urlsafe_b64encode(key).decode()

def create_secure_database_engine(database_url: str):
    """Create a secure database engine with proper security configurations."""

    # Parse database URL to ensure SSL
    if database_url.startswith('postgresql://'):
        # Upgrade to SSL connection
        if '?' in database_url:
            database_url += '&sslmode=require'
        else:
            database_url += '?sslmode=require'

    # Create engine with security settings
    engine = create_engine(
        database_url,
        # Security settings
        poolclass=NullPool,  # Disable connection pooling for security
        pool_pre_ping=True,  # Validate connections
        pool_recycle=3600,   # Recycle connections every hour
        echo=False,          # Don't log SQL queries (security risk)
        future=True,

        # Connection settings
        connect_args={
            "application_name": "codegenius_api",
            "connect_timeout": 10,
            "command_timeout": 30,
        } if 'postgresql' in database_url else {}
    )

    return engine

# SQL injection prevention
@event.listens_for(Engine, "before_cursor_execute")
def log_sql_queries(conn, cursor, statement, parameters, context, executemany):
    """Log and validate SQL queries for security monitoring."""
    # Only log in development
    if settings.debug:
        logger.debug(f"SQL Query: {statement}")

    # Check for dangerous patterns (additional safety net)
    dangerous_patterns = [
        'DROP TABLE',
        'DELETE FROM users',
        'TRUNCATE TABLE',
        'ALTER TABLE',
        'CREATE USER',
        'GRANT ALL',
    ]

    statement_upper = statement.upper()
    for pattern in dangerous_patterns:
        if pattern in statement_upper:
            logger.warning(f"Potentially dangerous SQL detected: {statement}")

class SecureSession:
    """Secure database session manager."""

    def __init__(self, engine):
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db_security = DatabaseSecurity()

    def get_db(self):
        """Get database session with security context."""
        db = self.SessionLocal()
        try:
            # Set session security parameters
            if 'postgresql' in str(db.bind.url):
                # PostgreSQL specific security settings
                db.execute("SET SESSION statement_timeout = '30s'")
                db.execute("SET SESSION idle_in_transaction_session_timeout = '5min'")
                db.execute("SET SESSION log_statement = 'none'")  # Don't log statements

            yield db
        except Exception as e:
            logger.error(f"Database session error: {e}")
            db.rollback()
            raise
        finally:
            db.close()

class AuditLog:
    """Security audit logging for database operations."""

    @staticmethod
    def log_user_action(user_id: int, action: str, resource: str, details: dict = None):
        """Log user actions for security audit."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': details or {},
            'ip_address': getattr(g, 'client_ip', 'unknown'),  # Get from request context
        }

        # In production, store in dedicated audit table
        logger.info(f"AUDIT: {json.dumps(log_entry)}")

    @staticmethod
    def log_security_event(event_type: str, severity: str, details: dict):
        """Log security events."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': details,
        }

        logger.warning(f"SECURITY_EVENT: {json.dumps(log_entry)}")

class DataMasking:
    """Data masking utilities for sensitive information."""

    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email address for logging/display."""
        if not email or '@' not in email:
            return email

        local, domain = email.rsplit('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]

        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_credit_card(card_number: str) -> str:
        """Mask credit card number."""
        if not card_number:
            return card_number

        # Remove spaces and non-digits
        digits_only = ''.join(filter(str.isdigit, card_number))

        if len(digits_only) < 8:
            return '*' * len(digits_only)

        # Show first 4 and last 4 digits
        return digits_only[:4] + '*' * (len(digits_only) - 8) + digits_only[-4:]

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """Mask API key for logging."""
        if not api_key:
            return api_key

        if len(api_key) <= 8:
            return '*' * len(api_key)

        return api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]

class DatabaseBackupSecurity:
    """Security measures for database backups."""

    def __init__(self, encryption_key: bytes):
        self.cipher_suite = Fernet(encryption_key)

    def encrypt_backup(self, backup_data: bytes) -> bytes:
        """Encrypt database backup."""
        return self.cipher_suite.encrypt(backup_data)

    def decrypt_backup(self, encrypted_backup: bytes) -> bytes:
        """Decrypt database backup."""
        return self.cipher_suite.decrypt(encrypted_backup)

    def generate_backup_checksum(self, backup_data: bytes) -> str:
        """Generate checksum for backup integrity verification."""
        import hashlib
        return hashlib.sha256(backup_data).hexdigest()

# Database connection security checks
def validate_database_security():
    """Validate database security configuration."""
    issues = []

    # Check SSL configuration
    if not settings.database_url.startswith('postgresql://') or 'sslmode=require' not in settings.database_url:
        issues.append("Database connection should use SSL")

    # Check for default passwords
    if 'password=password' in settings.database_url or 'password=admin' in settings.database_url:
        issues.append("Database is using default password")

    # Check encryption key
    if not os.getenv('DATABASE_ENCRYPTION_KEY'):
        issues.append("Database encryption key not configured")

    if issues:
        logger.warning(f"Database security issues found: {issues}")
        return False

    return True

# Initialize database security
db_security = DatabaseSecurity()

# Create secure engine
try:
    engine = create_secure_database_engine(settings.database_url)
    secure_session = SecureSession(engine)
except Exception as e:
    logger.error(f"Failed to create secure database connection: {e}")
    raise