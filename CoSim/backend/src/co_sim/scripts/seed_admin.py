from __future__ import annotations

import asyncio

from sqlalchemy import select

from co_sim.core.config import settings
from co_sim.db.session import async_session
from co_sim.models.user import User
from co_sim.services.password import get_password_hash

ADMIN_EMAIL = "admin@cosim.dev"
ADMIN_PASSWORD = "adminadmin"
ADMIN_FULL_NAME = "CoSim Admin"


async def seed_admin_user() -> None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        existing = result.scalar_one_or_none()
        if existing:
            if not existing.is_superuser:
                existing.is_superuser = True
                await session.commit()
            print(f"Admin user already exists: {ADMIN_EMAIL}")
            return

        user = User(
            email=ADMIN_EMAIL,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            full_name=ADMIN_FULL_NAME,
            is_active=True,
            is_superuser=True,
        )
        session.add(user)
        await session.commit()
        print(f"Created admin user {ADMIN_EMAIL} with password '{ADMIN_PASSWORD}'")


def main() -> None:
    print(f"Seeding admin user in environment '{settings.environment}'")
    asyncio.run(seed_admin_user())


if __name__ == "__main__":
    main()
