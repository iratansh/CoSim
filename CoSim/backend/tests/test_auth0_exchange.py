from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, select  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]

from co_sim.agents.auth.main import create_app  # type: ignore[import]
from co_sim.core.config import settings  # type: ignore[import]
from co_sim.models.user import User  # type: ignore[import]
from co_sim.services.auth0 import get_current_user_auth0  # type: ignore[import]


pytestmark = pytest.mark.asyncio(loop_scope="module")


SYNC_ENGINE = create_engine(settings.sync_database_uri, future=True)


def cleanup_user(email: str) -> None:
    with Session(SYNC_ENGINE) as session:
        session.execute(delete(User).where(User.email == email))
        session.commit()


def get_user(email: str) -> User | None:
    with Session(SYNC_ENGINE) as session:
        result = session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


def seed_user(**kwargs) -> User:
    user = User(**kwargs)
    with Session(SYNC_ENGINE) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@pytest.mark.asyncio
async def test_exchange_auth0_token_creates_or_updates_user() -> None:
    app = create_app()

    async def override_get_current_user_auth0() -> dict[str, str | bool]:
        return {
            "sub": "auth0|test-user",
            "email": "auth0_test@example.com",
            "name": "Auth0 Test",
            "nickname": "Auth0",
            "email_verified": True,
        }

    app.dependency_overrides[get_current_user_auth0] = override_get_current_user_auth0

    try:
        # Ensure a clean slate for this email before running the test
        cleanup_user("auth0_test@example.com")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response_first = await client.post("/v1/auth/auth0/exchange")
            response_second = await client.post("/v1/auth/auth0/exchange")

        assert response_first.status_code == 200
        assert response_second.status_code == 200

        payload = response_first.json()
        assert "access_token" in payload and payload["access_token"]
        assert payload["expires_in"] > 0

        user = get_user("auth0_test@example.com")
        assert user is not None
        assert user.external_id == "auth0|test-user"
        assert user.email_verified is True
        assert user.full_name == "Auth0 Test"
        assert user.hashed_password is None

        # Clean up created user for isolation
        cleanup_user("auth0_test@example.com")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_exchange_auth0_token_updates_existing_user() -> None:
    app = create_app()

    async def override_get_current_user_auth0() -> dict[str, str | bool]:
        return {
            "sub": "auth0|existing-user",
            "email": "auth0_existing@example.com",
            "name": "Updated Name",
            "nickname": "Updated",
            "email_verified": True,
        }

    app.dependency_overrides[get_current_user_auth0] = override_get_current_user_auth0

    try:
        # Seed an existing user without external_id to verify update path
        cleanup_user("auth0_existing@example.com")
        seed_user(
            email="auth0_existing@example.com",
            full_name="Old Name",
            email_verified=False,
            hashed_password="",
            plan="free",
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post("/v1/auth/auth0/exchange")

        assert response.status_code == 200

        user = get_user("auth0_existing@example.com")
        assert user is not None
        assert user.external_id == "auth0|existing-user"
        assert user.full_name == "Updated Name"
        assert user.email_verified is True
        assert user.hashed_password is None

        # Clean up seeded user
        cleanup_user("auth0_existing@example.com")
    finally:
        app.dependency_overrides.clear()
