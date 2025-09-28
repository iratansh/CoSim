from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time

from sqlalchemy.orm import Session
from core.db import get_db
from models.user import User, SubscriptionTier
from models.analysis_event import AnalysisEvent
from core.security import verify_token
from sqlalchemy import desc
from models.knowledge_document import KnowledgeDocument
from core.rag_scoring import relevance_score

from services.code_analysis_service import CodeAnalysisService
from services.github_service import GitHubService

router = APIRouter()

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str
    filename: Optional[str] = None
    context: Optional[str] = None

class PRAnalysisRequest(BaseModel):
    repo_url: str
    pr_number: int
    access_token: Optional[str] = None

class CodeSuggestion(BaseModel):
    line_number: int
    suggestion: str
    severity: str  # "info", "warning", "error"
    category: str  # "style", "performance", "security", "bug"

class AnalysisResponse(BaseModel):
    summary: str
    suggestions: List[CodeSuggestion]
    test_suggestions: Optional[List[str]] = None
    documentation_suggestions: Optional[List[str]] = None

def _extract_user(raw_request: Optional[Request], db: Session) -> Optional[User]:
    if not raw_request:
        return None
    auth_header = raw_request.headers.get("Authorization") or raw_request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    payload = verify_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    return db.query(User).filter(User.username == username).first()

def _enforce_quota(user: Optional[User]):
    if not user:
        return
    if user.subscription_tier == SubscriptionTier.FREE and not user.can_analyze():
        raise HTTPException(status_code=402, detail="Free tier monthly analysis limit reached. Upgrade to continue.")

def _record_analysis_event(db: Session, user: Optional[User], event_type: str, language: Optional[str], start_time: float, success: bool, error_code: Optional[str] = None, tokens_used: int = 0):
    duration_ms = int((time.time() - start_time) * 1000)
    evt = AnalysisEvent(
        user_id=user.id if user else None,
        type=event_type,
        language=language,
        duration_ms=duration_ms,
        success=success,
        error_code=error_code,
        tokens_used=tokens_used
    )
    db.add(evt)
    if user and success:
        user.monthly_analyses_used = (user.monthly_analyses_used or 0) + 1
        user.total_analyses = (user.total_analyses or 0) + 1
    db.commit()

@router.post("/analyze-code", response_model=AnalysisResponse)
async def analyze_code(
    request: CodeAnalysisRequest,
    analysis_service: CodeAnalysisService = Depends(),
    db: Session = Depends(get_db),
    raw_request: Request = None,
    response: Response = None
):
    """Analyze a code snippet and provide suggestions (enforces plan quota)."""
    start = time.time()
    user = _extract_user(raw_request, db)
    _enforce_quota(user)
    try:
        result = await analysis_service.analyze_code_snippet(
            code=request.code,
            language=request.language,
            filename=request.filename,
            context=request.context
        )
        # Attach RAG retrieval context (top 3 docs) if any documents exist
        docs = db.query(KnowledgeDocument).order_by(desc(KnowledgeDocument.created_at)).limit(250).all()
        if docs:
            scored = []
            for d in docs:
                score = relevance_score(request.code, d.content or '')
                if score > 0:
                    scored.append((score, d))
            scored.sort(key=lambda x: x[0], reverse=True)
            top = [
                {
                    'id': d.id,
                    'path': d.path,
                    'score': round(score,4),
                    'excerpt': (d.content[:180] + '...') if len(d.content) > 180 else d.content
                }
                for score, d in scored[:3]
            ]
            result['retrieval_context'] = top
        _record_analysis_event(db, user, "code", request.language, start, True)
        if user:
            # Set usage headers
            from core.plan_config import remaining_quota
            remaining = remaining_quota(user.subscription_tier.value, user.monthly_analyses_used or 0)
            limit = user.monthly_limit if not user.subscription_tier.name.lower() in ('professional','enterprise') else -1
            if response:
                response.headers['X-Usage-Limit'] = str(limit)
                response.headers['X-Usage-Remaining'] = str(remaining)
        return result
    except Exception as e:
        _record_analysis_event(db, user, "code", request.language, start, False, error_code="internal_error")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analyze-pr", response_model=Dict[str, Any])
async def analyze_pull_request(
    request: PRAnalysisRequest,
    analysis_service: CodeAnalysisService = Depends(),
    github_service: GitHubService = Depends(),
    db: Session = Depends(get_db),
    raw_request: Request = None,
    response: Response = None
):
    """Analyze a pull request and provide comprehensive review (enforces plan quota)."""
    start = time.time()
    user = _extract_user(raw_request, db)
    _enforce_quota(user)
    try:
        repo_parts = request.repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid repository URL")

        repo_full_name = f"{repo_parts[0]}/{repo_parts[1]}"
        pr_details = await github_service.get_pr_details(
            repo_full_name, request.pr_number, request.access_token
        )
        changed_files = await github_service.get_pr_changed_files(
            repo_full_name, request.pr_number, request.access_token
        )
        analysis_result = await analysis_service.analyze_pr_changes(
            repo_full_name,
            pr_details["base"]["sha"],
            pr_details["head"]["sha"],
            changed_files
        )
        payload = {
            "pr_details": pr_details,
            "analysis": analysis_result,
            "files_count": len(changed_files)
        }
        _record_analysis_event(db, user, "pr", None, start, True)
        if user:
            from core.plan_config import remaining_quota
            remaining = remaining_quota(user.subscription_tier.value, user.monthly_analyses_used or 0)
            limit = user.monthly_limit if not user.subscription_tier.name.lower() in ('professional','enterprise') else -1
            if response:
                response.headers['X-Usage-Limit'] = str(limit)
                response.headers['X-Usage-Remaining'] = str(remaining)
        return payload
    except Exception as e:
        _record_analysis_event(db, user, "pr", None, start, False, error_code="internal_error")
        raise HTTPException(status_code=500, detail=f"PR analysis failed: {str(e)}")

@router.post("/explain-code")
async def explain_code(
    request: CodeAnalysisRequest,
    analysis_service: CodeAnalysisService = Depends()
):
    """Provide natural language explanation of code."""
    try:
        explanation = await analysis_service.explain_code(
            code=request.code,
            language=request.language,
            context=request.context
        )
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code explanation failed: {str(e)}")

@router.post("/generate-tests")
async def generate_tests(
    request: CodeAnalysisRequest,
    analysis_service: CodeAnalysisService = Depends()
):
    """Generate unit tests for the provided code."""
    try:
        tests = await analysis_service.generate_tests(
            code=request.code,
            language=request.language,
            filename=request.filename
        )
        return {"tests": tests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")

@router.post("/generate-docs")
async def generate_documentation(
    request: CodeAnalysisRequest,
    analysis_service: CodeAnalysisService = Depends()
):
    """Generate documentation for the provided code."""
    try:
        docs = await analysis_service.generate_documentation(
            code=request.code,
            language=request.language,
            filename=request.filename
        )
        return {"documentation": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Documentation generation failed: {str(e)}")