from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Boolean
from sqlalchemy.sql import func
import enum

from models.base import Base


class KnowledgeDocType(enum.Enum):
    CODE = "code"
    DOC = "doc"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(512), index=True, nullable=False)
    doc_type = Column(Enum(KnowledgeDocType), nullable=False, index=True)
    language = Column(String(32), index=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    embedding_hash = Column(String(64), index=True)
    embedded = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<KnowledgeDocument id={self.id} path={self.path} type={self.doc_type.value}>"
