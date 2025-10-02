from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from co_sim.api.dependencies import get_current_user
from co_sim.models.user import User
from co_sim.schemas.collab import CollabDocumentCreate, CollabDocumentRead, CollabParticipant
from co_sim.services import collab as collab_service

router = APIRouter(prefix="/collab", tags=["collaboration"])


@router.post("/documents", response_model=CollabDocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: CollabDocumentCreate,
    _: Annotated[User, Depends(get_current_user)],
) -> CollabDocumentRead:
    return collab_service.create_document(payload)


@router.get("/documents/{document_id}", response_model=CollabDocumentRead)
async def get_document(
    document_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
) -> CollabDocumentRead:
    document = collab_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/documents/{document_id}/participants", response_model=CollabDocumentRead)
async def add_participant(
    document_id: UUID,
    payload: CollabParticipant,
    _: Annotated[User, Depends(get_current_user)],
) -> CollabDocumentRead:
    document = collab_service.add_participant(document_id, payload)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document
