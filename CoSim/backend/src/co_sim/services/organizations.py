from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.models.organization import Organization
from co_sim.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate


async def create_organization(session: AsyncSession, payload: OrganizationCreate) -> OrganizationRead:
    org = Organization(name=payload.name, slug=payload.slug, description=payload.description)
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return OrganizationRead.model_validate(org)


async def list_organizations(session: AsyncSession) -> list[OrganizationRead]:
    result = await session.execute(select(Organization))
    return [OrganizationRead.model_validate(org) for org in result.scalars().all()]


async def get_organization(session: AsyncSession, organization_id: UUID) -> Organization | None:
    result = await session.execute(select(Organization).where(Organization.id == organization_id))
    return result.scalar_one_or_none()


async def update_organization(
    session: AsyncSession, organization: Organization, payload: OrganizationUpdate
) -> OrganizationRead:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(organization, field, value)
    await session.commit()
    await session.refresh(organization)
    return OrganizationRead.model_validate(organization)
