from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.models.workspace_file import WorkspaceFile
from co_sim.schemas.workspace_file import WorkspaceFileRead, WorkspaceFileUpsert


async def list_workspace_files(session: AsyncSession, workspace_id: UUID) -> list[WorkspaceFileRead]:
    result = await session.execute(
        select(WorkspaceFile).where(WorkspaceFile.workspace_id == workspace_id).order_by(WorkspaceFile.path)
    )
    files = result.scalars().all()
    return [WorkspaceFileRead.model_validate(file) for file in files]


async def get_workspace_file(session: AsyncSession, workspace_id: UUID, path: str) -> WorkspaceFile | None:
    result = await session.execute(
        select(WorkspaceFile).where(
            WorkspaceFile.workspace_id == workspace_id,
            WorkspaceFile.path == path,
        )
    )
    return result.scalar_one_or_none()


async def upsert_workspace_file(
    session: AsyncSession, workspace_id: UUID, payload: WorkspaceFileUpsert
) -> WorkspaceFileRead:
    workspace_file = await get_workspace_file(session, workspace_id, payload.path)

    if workspace_file is None:
        workspace_file = WorkspaceFile(
            workspace_id=workspace_id,
            path=payload.path,
            content=payload.content,
            language=payload.language,
        )
        session.add(workspace_file)
    else:
        workspace_file.content = payload.content
        workspace_file.language = payload.language

    await session.commit()
    await session.refresh(workspace_file)
    return WorkspaceFileRead.model_validate(workspace_file)

