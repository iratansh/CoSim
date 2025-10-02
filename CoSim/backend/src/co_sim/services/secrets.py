from __future__ import annotations

import base64
import hashlib
from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.core.config import settings
from co_sim.models.secret import Secret
from co_sim.schemas.secret import SecretCreate, SecretRead, SecretReveal


def _build_cipher() -> Fernet:
    digest = hashlib.sha256(settings.jwt_secret_key.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


async def create_secret(session: AsyncSession, payload: SecretCreate) -> SecretRead:
    cipher = _build_cipher()
    encrypted = cipher.encrypt(payload.value.encode())
    secret = Secret(workspace_id=payload.workspace_id, name=payload.name, value_encrypted=encrypted.decode())
    session.add(secret)
    await session.commit()
    await session.refresh(secret)
    return SecretRead.model_validate(secret)


async def list_secrets(session: AsyncSession, workspace_id: UUID) -> list[SecretRead]:
    result = await session.execute(select(Secret).where(Secret.workspace_id == workspace_id))
    return [SecretRead.model_validate(secret) for secret in result.scalars().all()]


async def reveal_secret(session: AsyncSession, secret_id: UUID) -> SecretReveal | None:
    result = await session.execute(select(Secret).where(Secret.id == secret_id))
    secret = result.scalar_one_or_none()
    if not secret:
        return None
    cipher = _build_cipher()
    value = cipher.decrypt(secret.value_encrypted.encode()).decode()
    base = SecretRead.model_validate(secret)
    return SecretReveal(**base.model_dump(), value=value)


async def delete_secret(session: AsyncSession, secret_id: UUID) -> None:
    await session.execute(delete(Secret).where(Secret.id == secret_id))
    await session.commit()
