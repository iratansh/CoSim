"""
RAG-Enhanced Code Review API Routes
Provides endpoints for intelligent code review using Retrieval-Augmented Generation
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from core.rag_code_review import rag_engine, CodeContext, RetrievedContext
from core.security import get_current_user
from core.db import get_db
from sqlalchemy.orm import Session
from models.user import User
from core.plan_permissions import has_feature_access
from tasks.rag_tasks import index_codebase_task

logger = logging.getLogger(__name__)

router = APIRouter()


def _ensure_rag_access(username: str, db: Session) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not has_feature_access(user.subscription_tier, 'rag'):
        raise HTTPException(status_code=403, detail="Upgrade required for RAG features")
    return user

class RAGCodeAnalysisRequest(BaseModel):
    code: str = Field(..., description="Code to analyze")
    language: str = Field(..., description="Programming language")
    file_path: Optional[str] = Field(None, description="File path for context")
    include_similar_patterns: bool = Field(True, description="Include similar code patterns")
    include_documentation: bool = Field(True, description="Include relevant documentation")
    max_suggestions: int = Field(10, description="Maximum number of suggestions")

class CodebaseIndexRequest(BaseModel):
    repository_path: str = Field(..., description="Path to repository to index")
    force_reindex: bool = Field(False, description="Force complete reindexing")

class RAGSuggestion(BaseModel):
    type: str
    severity: str
    message: str
    context: str
    line_number: Optional[int] = None
    confidence_score: Optional[float] = None

class RAGAnalysisResponse(BaseModel):
    summary: str
    suggestions: List[RAGSuggestion]
    code_context: Dict[str, Any]
    rag_context: Dict[str, Any]
    similar_patterns: List[str]
    relevant_docs: List[str]
    processing_time_ms: int

class IndexingResponse(BaseModel):
    status: str
    indexed_files: int
    failed_files: int
    total_embeddings: int
    message: str

@router.post("/analyze-with-rag", response_model=RAGAnalysisResponse)
async def analyze_code_with_rag(
    request: RAGCodeAnalysisRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze code using RAG-enhanced review system

    This endpoint provides intelligent code analysis by:
    - Finding similar code patterns in the indexed codebase
    - Retrieving relevant documentation and best practices
    - Generating context-aware suggestions
    - Providing complexity and quality metrics
    """
    try:
        import time
        start_time = time.time()

        _ensure_rag_access(current_user, db)

        # Perform RAG-enhanced analysis
        review_result = await rag_engine.enhanced_code_review(
            code=request.code,
            language=request.language,
            context={"file_path": request.file_path}
        )

        # Retrieve additional context if requested
        similar_patterns = []
        relevant_docs = []

        if request.include_similar_patterns or request.include_documentation:
            retrieved_context = await rag_engine.retrieve_context(
                code=request.code,
                language=request.language
            )

            if request.include_similar_patterns:
                similar_patterns = retrieved_context.similar_code[:3]  # Top 3

            if request.include_documentation:
                relevant_docs = retrieved_context.documentation[:3]  # Top 3

        # Convert suggestions to response format
        suggestions = []
        for suggestion in review_result.get("enhanced_suggestions", []):
            suggestions.append(RAGSuggestion(
                type=suggestion["type"],
                severity=suggestion["severity"],
                message=suggestion["message"],
                context=suggestion["context"],
                confidence_score=0.8  # Default confidence
            ))

        # Limit suggestions as requested
        suggestions = suggestions[:request.max_suggestions]

        processing_time = int((time.time() - start_time) * 1000)

        # Generate summary
        summary = f"RAG-enhanced analysis completed for {request.language} code. "
        summary += f"Found {len(suggestions)} suggestions based on "
        summary += f"{len(similar_patterns)} similar patterns and "
        summary += f"{len(relevant_docs)} relevant documentation entries."

        return RAGAnalysisResponse(
            summary=summary,
            suggestions=suggestions,
            code_context=review_result.get("code_context", {}),
            rag_context=review_result.get("rag_context", {}),
            similar_patterns=similar_patterns,
            relevant_docs=relevant_docs,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"RAG analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/index-codebase", response_model=IndexingResponse)
async def index_codebase(
    request: CodebaseIndexRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Index a codebase for RAG-enhanced reviews

    This endpoint:
    - Crawls the specified repository
    - Extracts code patterns and documentation
    - Creates vector embeddings for semantic search
    - Stores everything in the vector database
    """
    try:
        _ensure_rag_access(current_user, db)

        task = index_codebase_task.delay(request.repository_path, request.force_reindex)

        return IndexingResponse(
            status="queued",
            indexed_files=0,
            failed_files=0,
            total_embeddings=0,
            message=f"Indexing queued (task id: {task.id}). This may take several minutes."
        )

    except Exception as e:
        logger.error(f"Failed to start indexing: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.get("/indexing-status")
async def get_indexing_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current status of the RAG indexing system"""
    try:
        _ensure_rag_access(current_user, db)

        if not rag_engine.chroma_client:
            return {
                "status": "not_initialized",
                "message": "RAG system not initialized. Install required dependencies.",
                "code_embeddings": 0,
                "doc_embeddings": 0
            }

        code_count = rag_engine.code_collection.count() if rag_engine.code_collection else 0
        doc_count = rag_engine.docs_collection.count() if rag_engine.docs_collection else 0

        return {
            "status": "ready",
            "message": "RAG system operational",
            "code_embeddings": code_count,
            "doc_embeddings": doc_count,
            "total_embeddings": code_count + doc_count
        }

    except Exception as e:
        logger.error(f"Failed to get indexing status: {e}")
        return {
            "status": "error",
            "message": f"Error getting status: {str(e)}",
            "code_embeddings": 0,
            "doc_embeddings": 0
        }

@router.post("/search-similar-code")
async def search_similar_code(
    code: str,
    language: str,
    max_results: int = 5,
    current_user = Depends(get_current_user)
):
    """Search for similar code patterns in the indexed codebase"""
    try:
        retrieved_context = await rag_engine.retrieve_context(
            code=code,
            language=language
        )

        return {
            "similar_code": retrieved_context.similar_code[:max_results],
            "similarity_scores": retrieved_context.similarity_scores[:max_results],
            "total_found": len(retrieved_context.similar_code)
        }

    except Exception as e:
        logger.error(f"Similar code search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/get-code-context")
async def get_code_context(
    code: str,
    language: str,
    file_path: str = "",
    current_user = Depends(get_current_user)
):
    """Extract detailed context information from code"""
    try:
        context = rag_engine.extract_code_context(
            code=code,
            language=language,
            file_path=file_path
        )

        return {
            "file_path": context.file_path,
            "function_name": context.function_name,
            "class_name": context.class_name,
            "imports": context.imports,
            "dependencies": context.dependencies,
            "language": context.language,
            "complexity_score": context.complexity_score
        }

    except Exception as e:
        logger.error(f"Context extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Context extraction failed: {str(e)}")

@router.delete("/clear-index")
async def clear_rag_index(current_user = Depends(get_current_user)):
    """Clear the RAG vector database (admin only)"""
    try:
        # This should be restricted to admin users
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        if rag_engine.chroma_client:
            # Reset collections
            rag_engine.chroma_client.reset()

            # Reinitialize
            rag_engine._init_vector_db()

        return {
            "status": "success",
            "message": "RAG index cleared successfully"
        }

    except Exception as e:
        logger.error(f"Failed to clear index: {e}")
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")

# Health check for RAG system
@router.get("/health")
async def rag_health_check():
    """Health check for RAG system components"""
    health_status = {
        "vector_db": "unknown",
        "embeddings_model": "unknown",
        "parsers": "unknown",
        "overall": "unknown"
    }

    try:
        # Check vector database
        if rag_engine.chroma_client:
            health_status["vector_db"] = "healthy"
        else:
            health_status["vector_db"] = "not_initialized"

        # Check embeddings model
        if rag_engine.embeddings_model:
            health_status["embeddings_model"] = "healthy"
        else:
            health_status["embeddings_model"] = "not_loaded"

        # Check parsers
        if rag_engine.parsers:
            health_status["parsers"] = "healthy"
        else:
            health_status["parsers"] = "not_initialized"

        # Overall status
        if all(status == "healthy" for status in health_status.values() if status != "unknown"):
            health_status["overall"] = "healthy"
        else:
            health_status["overall"] = "degraded"

    except Exception as e:
        health_status["overall"] = "error"
        health_status["error"] = str(e)

    return health_status
