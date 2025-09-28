from sqlalchemy.orm import declarative_base

# Single declarative Base for all ORM models
Base = declarative_base()

__all__ = ["Base"]
