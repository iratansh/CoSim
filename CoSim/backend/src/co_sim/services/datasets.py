from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.models.dataset import Dataset
from co_sim.schemas.dataset import DatasetCreate, DatasetRead, DatasetUpdate


async def create_dataset(session: AsyncSession, payload: DatasetCreate) -> DatasetRead:
    dataset = Dataset(
        organization_id=payload.organization_id,
        name=payload.name,
        uri=payload.uri,
        description=payload.description,
    )
    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)
    return DatasetRead.model_validate(dataset)


async def list_datasets(session: AsyncSession, organization_id: UUID | None = None) -> list[DatasetRead]:
    query = select(Dataset)
    if organization_id:
        query = query.where(Dataset.organization_id == organization_id)
    result = await session.execute(query)
    return [DatasetRead.model_validate(dataset) for dataset in result.scalars().all()]


async def get_dataset(session: AsyncSession, dataset_id: UUID) -> Dataset | None:
    result = await session.execute(select(Dataset).where(Dataset.id == dataset_id))
    return result.scalar_one_or_none()


async def update_dataset(session: AsyncSession, dataset: Dataset, payload: DatasetUpdate) -> DatasetRead:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dataset, field, value)
    await session.commit()
    await session.refresh(dataset)
    return DatasetRead.model_validate(dataset)


async def delete_dataset(session: AsyncSession, dataset_id: UUID) -> None:
    await session.execute(delete(Dataset).where(Dataset.id == dataset_id))
    await session.commit()
