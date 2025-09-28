from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
import hashlib

from sqlalchemy.orm import Session
from core.db import get_db
from models.knowledge_document import KnowledgeDocument, KnowledgeDocType
from models.user import User
from core.rag_scoring import relevance_score
from core.security import verify_token
from core.plan_permissions import has_feature_access

router = APIRouter()

class IngestDocumentRequest(BaseModel):
    path: str = Field(..., description="Logical path or identifier")
    content: str
    doc_type: KnowledgeDocType
    language: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    language: Optional[str] = None
    limit: int = 5

def _require_rag_user(request: Request, db: Session) -> User:
    auth_header = request.headers.get('Authorization') or request.headers.get('authorization')
    if not auth_header or not auth_header.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail='Authentication required')
    token = auth_header.split(' ',1)[1].strip()
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')
    username = payload.get('sub')
    user = db.query(User).filter(User.username == username).first() if username else None
    if not user:
        raise HTTPException(status_code=401, detail='Invalid user')
    if not has_feature_access(user.subscription_tier, 'rag'):
        raise HTTPException(status_code=403, detail='Upgrade required for RAG features')
    return user

@router.post('/ingest')
async def ingest_document(req: IngestDocumentRequest, request: Request, db: Session = Depends(get_db)):
    _require_rag_user(request, db)
    # Upsert by path + doc_type
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.path==req.path, KnowledgeDocument.doc_type==req.doc_type).first()
    token_count = len(req.content.split())
    embedding_hash = hashlib.sha256(req.content.encode()).hexdigest()
    if not doc:
        doc = KnowledgeDocument(
            path=req.path,
            doc_type=req.doc_type,
            language=req.language,
            content=req.content,
            token_count=token_count,
            embedding_hash=embedding_hash
        )
        db.add(doc)
    else:
        doc.content = req.content
        doc.language = req.language
        doc.token_count = token_count
        doc.embedding_hash = embedding_hash
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "path": doc.path, "doc_type": doc.doc_type.value, "token_count": doc.token_count}

@router.post('/search')
async def search_documents(req: SearchRequest, request: Request, db: Session = Depends(get_db)):
    _require_rag_user(request, db)
    # Jaccard-based relevance
    q = db.query(KnowledgeDocument)
    if req.language:
        q = q.filter(KnowledgeDocument.language == req.language)
    candidates = q.limit(200).all()
    scored = []
    for doc in candidates:
        score = relevance_score(req.query, doc.content or '')
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, doc in scored[:req.limit]:
        results.append({
            'id': doc.id,
            'path': doc.path,
            'doc_type': doc.doc_type.value,
            'language': doc.language,
            'score': round(score, 4),
            'excerpt': (doc.content[:200] + '...') if len(doc.content) > 200 else doc.content
        })
    return {"results": results, "count": len(results)}

@router.get('/list')
async def list_documents(request: Request, db: Session = Depends(get_db), limit: int = 50, offset: int = 0):
    _require_rag_user(request, db)
    q = db.query(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    total = q.count()
    docs = q.offset(offset).limit(limit).all()
    return {"total": total, "items": [
        {"id": d.id, "path": d.path, "doc_type": d.doc_type.value, "language": d.language, "token_count": d.token_count, "embedded": d.embedded}
        for d in docs
    ]}

@router.delete('/{doc_id}')
async def delete_document(doc_id: int, request: Request, db: Session = Depends(get_db)):
    _require_rag_user(request, db)
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "id": doc_id}
