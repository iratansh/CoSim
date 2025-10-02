from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.models.template import Template
from co_sim.schemas.template import TemplateCreate, TemplateRead, TemplateUpdate


async def create_template(session: AsyncSession, payload: TemplateCreate) -> TemplateRead:
    template = Template(
        name=payload.name,
        kind=payload.kind,
        description=payload.description,
        config=payload.config,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return TemplateRead.model_validate(template)


async def list_templates(session: AsyncSession, kind: str | None = None) -> list[TemplateRead]:
    query = select(Template)
    if kind:
        query = query.where(Template.kind == kind)
    result = await session.execute(query)
    return [TemplateRead.model_validate(template) for template in result.scalars().all()]


async def get_template(session: AsyncSession, template_id: UUID) -> Template | None:
    result = await session.execute(select(Template).where(Template.id == template_id))
    return result.scalar_one_or_none()


async def update_template(session: AsyncSession, template: Template, payload: TemplateUpdate) -> TemplateRead:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    await session.commit()
    await session.refresh(template)
    return TemplateRead.model_validate(template)


async def delete_template(session: AsyncSession, template_id: UUID) -> None:
    await session.execute(delete(Template).where(Template.id == template_id))
    await session.commit()
