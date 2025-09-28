from __future__ import annotations
import hmac
import hashlib
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from core.config import get_settings

settings = get_settings()

DEFAULT_EXP_MINUTES_EMAIL = 60
DEFAULT_EXP_MINUTES_RESET = 30

def _sign(payload: dict, secret: str) -> str:
    data = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode()
    sig = hmac.new(secret.encode(), data, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(data + b'.' + sig).decode()

def _unsign(token: str, secret: str) -> Optional[dict]:
    try:
        raw = base64.urlsafe_b64decode(token.encode())
        data, sig = raw.rsplit(b'.', 1)
        expected = hmac.new(secret.encode(), data, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(data.decode())
        exp = payload.get('exp')
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            return None
        return payload
    except Exception:
        return None

def generate_email_verification_token(user_id: int, email: str, expires_minutes: int = DEFAULT_EXP_MINUTES_EMAIL) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {
        'sub': user_id,
        'email': email,
        'type': 'email_verify',
        'exp': int(exp.timestamp())
    }
    return _sign(payload, settings.jwt_secret_key)

def verify_email_token(token: str) -> Optional[dict]:
    payload = _unsign(token, settings.jwt_secret_key)
    if not payload or payload.get('type') != 'email_verify':
        return None
    return payload

def generate_password_reset_token(user_id: int, email: str, expires_minutes: int = DEFAULT_EXP_MINUTES_RESET) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {
        'sub': user_id,
        'email': email,
        'type': 'password_reset',
        'exp': int(exp.timestamp())
    }
    return _sign(payload, settings.jwt_secret_key)

def verify_password_reset_token(token: str) -> Optional[dict]:
    payload = _unsign(token, settings.jwt_secret_key)
    if not payload or payload.get('type') != 'password_reset':
        return None
    return payload

__all__ = [
    'generate_email_verification_token',
    'verify_email_token',
    'generate_password_reset_token',
    'verify_password_reset_token'
]