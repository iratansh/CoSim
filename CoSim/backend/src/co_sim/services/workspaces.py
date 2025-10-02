from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.models.workspace import Workspace, WorkspaceStatus
from co_sim.schemas.workspace import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate


async def create_workspace(session: AsyncSession, payload: WorkspaceCreate) -> WorkspaceRead:
    workspace = Workspace(
        project_id=payload.project_id,
        template_id=payload.template_id,
        name=payload.name,
        slug=payload.slug,
        requested_gpu=payload.requested_gpu,
        settings=payload.settings,
    )
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    return WorkspaceRead.model_validate(workspace)


async def list_workspaces(session: AsyncSession, project_id: UUID | None = None) -> list[WorkspaceRead]:
    query = select(Workspace)
    if project_id:
        query = query.where(Workspace.project_id == project_id)
    result = await session.execute(query)
    return [WorkspaceRead.model_validate(workspace) for workspace in result.scalars().all()]


async def get_workspace(session: AsyncSession, workspace_id: UUID) -> Workspace | None:
    result = await session.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def update_workspace(session: AsyncSession, workspace: Workspace, payload: WorkspaceUpdate) -> WorkspaceRead:
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is None:
        data.pop("status")
    for field, value in data.items():
        setattr(workspace, field, value)
    await session.commit()
    await session.refresh(workspace)
    return WorkspaceRead.model_validate(workspace)


async def delete_workspace(session: AsyncSession, workspace_id: UUID) -> None:
    await session.execute(delete(Workspace).where(Workspace.id == workspace_id))
    await session.commit()


async def transition_workspace_status(
    session: AsyncSession, workspace: Workspace, status: WorkspaceStatus
) -> WorkspaceRead:
    workspace.status = status
    await session.commit()
    await session.refresh(workspace)
    return WorkspaceRead.model_validate(workspace)
