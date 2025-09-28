"""Celery tasks for maintaining the RAG knowledge base."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

from celery import states

from celery_app import celery
from core.rag_code_review import rag_engine


logger = logging.getLogger(__name__)


@celery.task(name="codegenius.rag.index_codebase", bind=True)
def index_codebase_task(self, repository_path: str, force_reindex: bool = False) -> Dict[str, int]:
    """Index a repository path and persist embeddings."""
    try:
        if force_reindex:
            rag_engine.reset_collections()
        result = asyncio.run(rag_engine.index_codebase(repository_path))
        rag_engine.persist_embeddings()
        return {
            'indexed_files': result.get('indexed_files', 0),
            'failed_files': result.get('failed_files', 0),
            'total_embeddings': result.get('total_code_embeddings', 0) + result.get('total_doc_embeddings', 0),
        }
    except Exception as exc:  # pragma: no cover - Celery surfaces via task state
        logger.error("RAG indexing task failed: %s", exc)
        self.update_state(state=states.FAILURE, meta={'exc': str(exc)})
        raise


@celery.task(name="codegenius.rag.persist")
def persist_embeddings_task() -> str:
    """Force a persistence sync of the vector database."""
    rag_engine.persist_embeddings()
    return "persisted"
