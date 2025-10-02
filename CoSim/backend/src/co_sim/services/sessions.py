from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.models.session import Session, SessionParticipant, SessionStatus
from co_sim.schemas.session import (
    SessionCreate,
    SessionParticipantCreate,
    SessionParticipantRead,
    SessionRead,
    SessionUpdate,
)


async def create_session(session: AsyncSession, payload: SessionCreate) -> SessionRead:
    db_session = Session(
        workspace_id=payload.workspace_id,
        session_type=payload.session_type,
        requested_gpu=payload.requested_gpu,
        details=payload.details,
    )
    session.add(db_session)
    await session.commit()
    await session.refresh(db_session)
    return await serialize_session(session, db_session)


async def list_sessions(
    session: AsyncSession,
    workspace_id: UUID | None = None,
    status: SessionStatus | None = None,
) -> list[SessionRead]:
    query = select(Session)
    if workspace_id:
        query = query.where(Session.workspace_id == workspace_id)
    if status:
        query = query.where(Session.status == status)
    result = await session.execute(query)
    sessions = result.scalars().all()
    return [await serialize_session(session, s) for s in sessions]


async def get_session(session: AsyncSession, session_id: UUID) -> Session | None:
    result = await session.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def update_session(
    session: AsyncSession,
    db_session: Session,
    payload: SessionUpdate,
) -> SessionRead:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_session, field, value)
    if "status" in data and data["status"] in {SessionStatus.RUNNING, SessionStatus.STARTING}:
        db_session.started_at = datetime.now(timezone.utc)
    if "status" in data and data["status"] in {SessionStatus.TERMINATED}:
        db_session.ended_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(db_session)
    return await serialize_session(session, db_session)


async def transition_status(
    session: AsyncSession,
    db_session: Session,
    status: SessionStatus,
) -> SessionRead:
    return await update_session(session, db_session, SessionUpdate(status=status))


async def add_participant(
    session: AsyncSession,
    db_session: Session,
    payload: SessionParticipantCreate,
) -> SessionParticipantRead:
    participant = SessionParticipant(session_id=db_session.id, user_id=payload.user_id, role=payload.role)
    session.add(participant)
    await session.commit()
    await session.refresh(participant)
    return SessionParticipantRead.model_validate(participant)


async def serialize_session(session: AsyncSession, db_session: Session) -> SessionRead:
    await session.refresh(db_session, attribute_names=["participants"])
    participants = [SessionParticipantRead.model_validate(p) for p in db_session.participants]
    base = SessionRead.model_validate(db_session)
    return base.model_copy(update={"participants": participants})
