from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.models.project import Project
from co_sim.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate


async def create_project(session: AsyncSession, payload: ProjectCreate, creator_id: UUID | None) -> ProjectRead:
    project = Project(
        organization_id=payload.organization_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        template_id=payload.template_id,
        settings=payload.settings,
        created_by_id=creator_id,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return ProjectRead.model_validate(project)


async def list_projects(session: AsyncSession, organization_id: UUID | None = None) -> list[ProjectRead]:
    query = select(Project)
    if organization_id:
        query = query.where(Project.organization_id == organization_id)
    result = await session.execute(query)
    return [ProjectRead.model_validate(project) for project in result.scalars().all()]


async def get_project(session: AsyncSession, project_id: UUID) -> Project | None:
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def update_project(session: AsyncSession, project: Project, payload: ProjectUpdate) -> ProjectRead:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await session.commit()
    await session.refresh(project)
    return ProjectRead.model_validate(project)


async def delete_project(session: AsyncSession, project_id: UUID) -> None:
    await session.execute(delete(Project).where(Project.id == project_id))
    await session.commit()
