"""Authentication service helpers to keep route layer slim."""

from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import jwt

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - redis optional in local dev
    redis = None

from core.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()

redis_client = None
USE_REDIS = False
session_store: Dict[str, Dict] = {}
failed_attempts: Dict[str, int] = {}
revoked_jtis = set()

if redis and settings.redis_url:
    try:
        redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        USE_REDIS = True
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Redis unavailable for auth service: %s", exc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SessionService:
    """Encapsulates secure session creation and validation."""

    def __init__(self):
        self.session_duration = timedelta(hours=24)
        self.refresh_duration = timedelta(days=30)

    def create_session(self, user_id: int, ip_address: str, user_agent: str, remember_me: bool = False) -> Dict[str, str]:
        session_id = secrets.token_urlsafe(32)
        access_token = self._create_token('access', user_id, session_id, minutes=15)
        refresh_token = self._create_token('refresh', user_id, session_id, days=30)

        duration = self.refresh_duration if remember_me else self.session_duration
        session_payload = {
            'user_id': user_id,
            'session_id': session_id,
            'ip_address': ip_address,
            'user_agent': user_agent[:200],
            'created_at': _now().isoformat(),
            'expires_at': (_now() + duration).isoformat(),
            'remember_me': remember_me,
            'active': True,
        }

        if USE_REDIS and redis_client:
            redis_client.setex(f"session:{session_id}", int(duration.total_seconds()), json.dumps(session_payload))
        else:
            session_store[session_id] = session_payload

        return {
            'session_id': session_id,
            'access_token': access_token,
            'refresh_token': refresh_token,
        }

    def issue_access_token(self, user_id: int, session_id: str) -> str:
        """Generate a new short-lived access token for an existing session."""
        return self._create_token('access', user_id, session_id, minutes=15)

    def _create_token(self, token_type: str, user_id: int, session_id: str, *, minutes: int = 0, days: int = 0) -> str:
        expires = _now() + timedelta(minutes=minutes, days=days)
        payload = {
            'sub': str(user_id),
            'session_id': session_id,
            'type': token_type,
            'exp': expires,
            'iat': _now(),
            'jti': secrets.token_urlsafe(16),
            'aud': 'codegenius-api',
            'iss': 'codegenius.ai',
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def validate_session(self, session_id: str, ip_address: str) -> Optional[Dict]:
        try:
            if USE_REDIS and redis_client:
                raw = redis_client.get(f"session:{session_id}")
                if not raw:
                    return None
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    return None
            else:
                data = session_store.get(session_id)

            if not data or not data.get('active'):
                return None

            expires_at = datetime.fromisoformat(data['expires_at'])
            if _now() > expires_at:
                self.invalidate_session(session_id)
                return None

            if settings.strict_ip_validation and data.get('ip_address') != ip_address:
                return None

            return data
        except Exception as exc:  # pragma: no cover - defensive safeguard
            logger.error("Session validation error: %s", exc)
            return None

    def invalidate_session(self, session_id: str) -> None:
        if USE_REDIS and redis_client:
            redis_client.delete(f"session:{session_id}")
        else:
            session_store.pop(session_id, None)

    def invalidate_all_sessions(self, user_id: int) -> None:
        if USE_REDIS and redis_client:
            pattern = "session:*"
            for key in redis_client.scan_iter(pattern):
                payload = json.loads(redis_client.get(key) or '{}')
                if payload.get('user_id') == user_id:
                    redis_client.delete(key)
        else:
            for sid in list(session_store.keys()):
                if session_store[sid].get('user_id') == user_id:
                    session_store.pop(sid, None)


class BruteForceProtectionService:
    """Protects against brute force login attempts."""

    def __init__(self):
        self.max_attempts = 5
        self.lockout_seconds = 900

    def check(self, identifier: str) -> Dict[str, int | bool]:
        key = f"login_attempts:{identifier}"
        attempts = 0
        if USE_REDIS and redis_client:
            attempts_raw = redis_client.get(key)
            attempts = int(attempts_raw) if attempts_raw else 0
        else:
            attempts = failed_attempts.get(identifier, 0)

        blocked = attempts >= self.max_attempts
        return {
            'blocked': blocked,
            'attempts': attempts,
            'retry_after': self.lockout_seconds,
        }

    def record_failure(self, identifier: str) -> None:
        key = f"login_attempts:{identifier}"
        if USE_REDIS and redis_client:
            redis_client.incr(key)
            redis_client.expire(key, self.lockout_seconds)
        else:
            failed_attempts[identifier] = failed_attempts.get(identifier, 0) + 1

    def reset(self, identifier: str) -> None:
        key = f"login_attempts:{identifier}"
        if USE_REDIS and redis_client:
            redis_client.delete(key)
        else:
            failed_attempts.pop(identifier, None)


SESSION_SERVICE = SessionService()
BRUTE_FORCE_SERVICE = BruteForceProtectionService()


TOKEN_DENYLIST_PREFIX = "revoked:jti:"


def add_jti_to_denylist(jti: str, exp: int) -> None:
    ttl = max(exp - int(_now().timestamp()), 0)
    if USE_REDIS and redis_client:
        redis_client.setex(f"{TOKEN_DENYLIST_PREFIX}{jti}", ttl or 1, "1")
    else:
        revoked_jtis.add(jti)


def is_jti_revoked(jti: str) -> bool:
    if USE_REDIS and redis_client:
        return bool(redis_client.get(f"{TOKEN_DENYLIST_PREFIX}{jti}"))
    return jti in revoked_jtis


__all__ = [
    'SESSION_SERVICE',
    'BRUTE_FORCE_SERVICE',
    'add_jti_to_denylist',
    'is_jti_revoked',
    'USE_REDIS',
    'redis_client',
]
