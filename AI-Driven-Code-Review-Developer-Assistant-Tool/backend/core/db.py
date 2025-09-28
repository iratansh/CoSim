from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, echo=settings.debug, future=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True))

from models.base import Base  # unified Base

@contextmanager
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create database tables based on models (idempotent)."""
    # Import models to register metadata
    import models.user  # noqa: F401
    import models.analysis_event  # noqa: F401
    import models.knowledge_document  # noqa: F401
    Base.metadata.create_all(bind=engine)
