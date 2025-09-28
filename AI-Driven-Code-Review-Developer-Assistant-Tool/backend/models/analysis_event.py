from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from models.base import Base
from models.user import User

class AnalysisEvent(Base):
    __tablename__ = "analysis_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    type = Column(String(32), nullable=False)  # code|pr|tests|docs
    language = Column(String(32), nullable=True)
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_code = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User", backref="analysis_events")
