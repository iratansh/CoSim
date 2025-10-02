from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from co_sim.schemas.collab import CollabDocumentCreate, CollabDocumentRead, CollabParticipant


@dataclass
class CollabDocumentState:
    document_id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None = None
    template_path: str | None = None
    participants: List[CollabParticipant] = field(default_factory=list)


_documents: Dict[uuid.UUID, CollabDocumentState] = {}
_lock = threading.Lock()


def create_document(payload: CollabDocumentCreate) -> CollabDocumentRead:
    document_id = uuid.uuid4()
    state = CollabDocumentState(
        document_id=document_id,
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        template_path=payload.template_path,
    )
    with _lock:
        _documents[document_id] = state
    return CollabDocumentRead(**state.__dict__)


def get_document(document_id: uuid.UUID) -> CollabDocumentRead | None:
    with _lock:
        state = _documents.get(document_id)
        if not state:
            return None
        return CollabDocumentRead(**state.__dict__)


def add_participant(document_id: uuid.UUID, participant: CollabParticipant) -> CollabDocumentRead | None:
    with _lock:
        state = _documents.get(document_id)
        if not state:
            return None
        state.participants = [p for p in state.participants if p.user_id != participant.user_id]
        state.participants.append(participant)
        return CollabDocumentRead(**state.__dict__)
